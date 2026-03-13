import re

class ApexSpreadsheetProcessor:
    def __init__(self, service, spreadsheet_id):
        self.service = service
        self.spreadsheet_id = spreadsheet_id

    def _get_target_sheet_id(self, sheet_name):
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        for sheet in spreadsheet.get('sheets', []):
            if sheet.get('properties', {}).get('title') == sheet_name:
                return sheet.get('properties', {}).get('sheetId')
        return None

    def append_results(self, sheet_name, match_id, data_list):
        target_sid = self._get_target_sheet_id(sheet_name)
        
        rows = [[match_id, d['rank'], d['team_name'], d['kills']] for d in data_list]

        body = {'values': rows}
        res = self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id, 
            range=f"'{sheet_name}'!A3:D", 
            valueInputOption="USER_ENTERED", 
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        updated_range = res.get('updates', {}).get('updatedRange', '')
        match = re.search(r'!A(\d+)', updated_range)
        if not match: return res
        start_row_idx = int(match.group(1)) - 1

        requests = []
        for i, d in enumerate(data_list):
            color = {"red": 1.0, "green": 1.0, "blue": 1.0} 
            
            if d.get('is_anomaly'):
                color = {"red": 1.0, "green": 0.8, "blue": 0.8}
            elif d.get('is_corrected'):
                color = {"red": 1.0, "green": 0.9, "blue": 0.7}

            row = start_row_idx + i
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": target_sid,
                        "startRowIndex": row, "endRowIndex": row + 1,
                        "startColumnIndex": 0, "endColumnIndex": 4
                    },
                    "cell": {
                        "userEnteredFormat": {"backgroundColor": color}
                    },
                    "fields": "userEnteredFormat.backgroundColor"
                }
            })

        if requests:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        return res