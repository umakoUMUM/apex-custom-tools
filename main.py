import os
import shutil
import re
import yaml
from dotenv import load_dotenv
from google.cloud import vision
from google.oauth2 import service_account
from googleapiclient.discovery import build

from image_processor import ApexImageProcessor
from ocr_processor import ApexOcrProcessor
from spreadsheet_processor import ApexSpreadsheetProcessor

load_dotenv()

def run_production_flow():
    # --- 設定の読み込み ---
    CONFIG_PATH = "config.yaml"
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ エラー: {CONFIG_PATH} が見つかりません。")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f)

    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID") or CONFIG.get('spreadsheet', {}).get('id')
    JSON_KEY = "credentials.json" 
    
    if not os.path.exists(JSON_KEY):
        print(f"❌ エラー: {JSON_KEY} が見つかりません。")
        return

    if not SPREADSHEET_ID:
        print("❌ エラー: スプレッドシートIDが設定されていません。")
        return

    os.makedirs(CONFIG['settings']['PROCESSED_DIR'], exist_ok=True)

    # 認証
    creds = service_account.Credentials.from_service_account_file(
        JSON_KEY, 
        scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/cloud-vision']
    )
    sheets_service = build('sheets', 'v4', credentials=creds)
    vision_client = vision.ImageAnnotatorClient(credentials=creds)

    img_proc = ApexImageProcessor(CONFIG)
    ocr_proc = ApexOcrProcessor(vision_client)
    sheet_proc = ApexSpreadsheetProcessor(sheets_service, SPREADSHEET_ID)

    # --- 画像の順次処理 ---
    target_dir = CONFIG['settings']['SCREENSHOTS_DIR']
    files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not files:
        print("📁 処理待ちの画像は見つかりませんでした。")
        return

    for filename in files:
        img_path = os.path.join(target_dir, filename)
        match_id_match = re.search(r'\d+', filename)
        match_id = match_id_match.group() if match_id_match else filename
        
        print(f"\n🎮 Match {match_id} の解析を開始します...")

        fragments = img_proc.get_all_fragments(img_path)[:CONFIG['match_settings']['TOTAL_TEAMS']]
        raw_results = ocr_proc.process_all_results(fragments)
        
        final_data = []
        for i, r in enumerate(raw_results):
            # 各セルごとのフラグを初期化
            r['rank_is_corrected'] = False
            r['kills_is_corrected'] = False
            r['kills_is_anomaly'] = False
            
            # 1. 順位の補完チェック
            expected_rank = i + 1
            if r['rank'] != expected_rank:
                r['rank'] = expected_rank
                r['rank_is_corrected'] = True # 順位だけをフラグ立て
            
            # 2. キル数の補正 (60 -> 9)
            if r['kills'] == 60:
                r['kills'] = 9
                r['kills_is_corrected'] = True # キル数だけをフラグ立て
            
            # 3. 異常チェック (20以上)
            if (r['kills'] or 0) >= 20:
                r['kills_is_anomaly'] = True # キル数だけを異常フラグ立て

            final_data.append(r)

        print(f"  📝 '{CONFIG['settings']['RAW_DATA_SHEET']}' へ追記中...")
        sheet_proc.append_results(CONFIG['settings']['RAW_DATA_SHEET'], match_id, final_data)

        dest_path = os.path.join(CONFIG['settings']['PROCESSED_DIR'], filename)
        if os.path.exists(dest_path):
            os.remove(dest_path)
        shutil.move(img_path, dest_path)
        print(f"  📦 移動完了: {dest_path}")

    print("\n" + "="*50)
    print("🏆 システム実行完了！")
    print("="*50)

if __name__ == "__main__":
    run_production_flow()