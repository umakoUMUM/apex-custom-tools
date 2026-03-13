import os
import cv2
from image_processor import ApexImageProcessor

def run_visual_check(image_path):
    # 設定のダミー
    config = {
        'settings': {'base_resolution': {'width': 1920, 'height': 1080}},
        'match_settings': {'TOTAL_TEAMS': 17}
    }
    
    processor = ApexImageProcessor(config)
    
    # フォルダのクリーンアップ
    debug_dir = "debug_crops"
    if os.path.exists(debug_dir):
        import shutil
        shutil.rmtree(debug_dir)
    os.makedirs(debug_dir, exist_ok=True)

    print(f"🧐 画像 {image_path} を切り出し中...")
    
    # 全スロットの断片を取得
    fragments_list = processor.get_all_fragments(image_path)
    
    for i, fragments in enumerate(fragments_list):
        team_no = i + 1
        for field, img in fragments.items():
            fname = f"team_{team_no:02d}_{field}.png"
            # image_processorがRGBで返している場合はBGRに戻して保存
            save_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(os.path.join(debug_dir, fname), save_img)
            
    print(f"✅ {debug_dir} フォルダに全画像を保存しました。中身を確認してください！")

if __name__ == "__main__":
    run_visual_check(os.path.join("screenshots", "Match03.png"))