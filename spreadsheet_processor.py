import re

class ApexSpreadsheetProcessor:
    def __init__(self, service, spreadsheet_id):
        self.service = service
        self.spreadsheet_id = spreadsheet_id

    def _get_target_sheet_id(self, sheet_name):
        """スプレッドシートの全シートをスキャンして正しいIDを見つける"""
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        for sheet in spreadsheet.get('sheets', []):
            if sheet.get('properties', {}).get('title') == sheet_name:
                return sheet.get('properties', {}).get('sheetId')
        return None

    def _create_color_request(self, sheet_id, row, start_col, end_col, color):
        """指定したセル範囲に背景色を塗るリクエストを作成する補助関数"""
        return {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row, "endRowIndex": row + 1,
                    "startColumnIndex": start_col, "endColumnIndex": end_col
                },
                "cell": {
                    "userEnteredFormat": {"backgroundColor": color}
                },
                "fields": "userEnteredFormat.backgroundColor"
            }
        }

    def append_results(self, sheet_name, match_id, data_list):
        target_sid = self._get_target_sheet_id(sheet_name)
        
        # 1. データの準備 (MatchID, 順位, チーム名, キル数)
        rows = [[match_id, d['rank'], d['team_name'], d['kills']] for d in data_list]

        # 2. 追記実行 (A3以降の空行に挿入)
        body = {'values': rows}
        res = self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id, 
            range=f"'{sheet_name}'!A3:D", 
            valueInputOption="USER_ENTERED", 
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        # 3. 追記範囲（行番号）の特定
        updated_range = res.get('updates', {}).get('updatedRange', '')
        match = re.search(r'!A(\d+)', updated_range)
        if not match: return res
        start_row_idx = int(match.group(1)) - 1

        # 4. 書式変更 (セル単位の塗り分け)
        requests = []
        # 色の定義
        orange = {"red": 1.0, "green": 0.9, "blue": 0.7}
        red = {"red": 1.0, "green": 0.8, "blue": 0.8}
        white = {"red": 1.0, "green": 1.0, "blue": 1.0}

        for i, d in enumerate(data_list):
            row = start_row_idx + i
            
            # --- 1. まず行全体 (A:0 〜 D:4) を白でリセットして「引きずり」を防止 ---
            requests.append(self._create_color_request(target_sid, row, 0, 4, white))

            # --- 2. 順位セル (B列: index 1) の着色 ---
            if d.get('rank_is_corrected'):
                requests.append(self._create_color_request(target_sid, row, 1, 2, orange))

            # --- 3. キル数セル (D列: index 3) の着色 ---
            if d.get('kills_is_anomaly'):
                # 異常（20以上）は赤色
                requests.append(self._create_color_request(target_sid, row, 3, 4, red))
            elif d.get('kills_is_corrected'):
                # 補正（60->9）はオレンジ色
                requests.append(self._create_color_request(target_sid, row, 3, 4, orange))

        if requests:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        return res