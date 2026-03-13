import io
import re
import logging
import cv2
from google.cloud import vision

# ログ設定：数値化失敗時などに詳細を記録
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ApexOcrProcessor:
    def __init__(self, client):
        """
        Vision APIクライアントを受け取り初期化
        """
        self.client = client
        # 数字の誤認識補正マップ (PM指示分 + アルファ)
        self.replacement_map = {
            'O': '0', 'o': '0',
            'I': '1', 'l': '1', 'i': '1', '|': '1',
            'S': '5', 's': '5',
            'B': '8', 'G': '6'
        }

    def _clean_numeric(self, text, field_name, team_no):
        if not text: return 0
        
        # 1. 置換マップ適用（PM指示分）
        cleaned = text
        for char, digit in self.replacement_map.items():
            cleaned = cleaned.replace(char, digit)

        # 2. 数字だけを抽出（余計な記号を無視）
        nums = re.findall(r'\d+', cleaned)
        if not nums: return 0
        
        # 3. 順位が「0」になった場合はチーム番号をフォールバック（完走優先）
        val = int("".join(nums))
        if field_name == "順位" and val == 0:
            return team_no
            
        return val

    def _clean_team_name(self, text, team_no):
        """
        チーム名用の補正ロジック
        仕様：「チーム」+「番号」の形式に整える
        """
        if not text:
            return f"チーム{team_no}" # 読み取れなかった場合のフォールバック

        # 文字列から数字を抽出
        nums = "".join(re.findall(r'\d+', text))
        
        if nums:
            return f"チーム{nums}"
        
        # 数字が全く取れなかった場合は、OCR結果をそのまま返すか
        # もしくはteam_noを使って「チームX」とする
        return text.strip()

    def recognize_team_data(self, image_fragments, team_idx):
        """
        1チーム分の画像断片（辞書）をOCRにかけ、整形済みデータを返す
        image_fragments: {'rank': img, 'name': img, 'kills': img}
        team_idx: 0〜19 (内部処理用インデックス)
        """
        team_no = team_idx + 1
        team_data = {
            "team_no": team_no,
            "rank": None,
            "team_name": "",
            "kills": 0
        }

        for field, img in image_fragments.items():
            # OpenCV画像をバイトデータに変換
            _, buffer = cv2.imencode(".png", img)
            content = buffer.tobytes()
            
            image = vision.Image(content=content)
            
            # ドキュメントテキスト検出モード（小さな文字に強い）
            response = self.client.document_text_detection(image=image)
            raw_text = response.full_text_annotation.text.strip() if response.full_text_annotation else ""

            # フィールドごとに補正ロジックを使い分ける
            if field == "rank":
                team_data["rank"] = self._clean_numeric(raw_text, "順位", team_no)
            elif field == "kills":
                team_data["kills"] = self._clean_numeric(raw_text, "キル数", team_no)
            elif field == "name":
                team_data["team_name"] = self._clean_team_name(raw_text, team_no)

        return team_data

    def process_all_results(self, all_team_fragments):
        """
        全20チームの画像断片リストを一括処理する
        all_team_fragments: [{'rank': img, 'name': img, 'kills': img}, ...] (20要素)
        """
        final_results = []
        print(f"\n--- OCR解析を開始します (全{len(all_team_fragments)}チーム) ---")
        
        for i, fragments in enumerate(all_team_fragments):
            result = self.recognize_team_data(fragments, i)
            final_results.append(result)
            
            # 進捗をコンソールに表示
            print(f"解析中... [{i+1:02d}/20] {result['team_name']}: Rank {result['rank']}, Kills {result['kills']}")
            
        print("--- 解析完了 ---\n")
        return final_results