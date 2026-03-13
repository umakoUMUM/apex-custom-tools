import cv2
import numpy as np

class ApexImageProcessor:
    def __init__(self, config):
        self.target_w = config['settings']['base_resolution']['width']
        self.target_h = config['settings']['base_resolution']['height']
        
        # 横方向の設定（PM指示：左右に0.5%ずつの遊びを追加）
        self.x_left_base = 17.5
        self.x_right_base = 58
        self.fields = {
            "rank":  {"width": 3,  "offset_x": 0.0},  # offset_xを-0.5, widthを+1.0
            "name":  {"width": 10.0, "offset_x": 3.5},
            "kills": {"width": 2.5,  "offset_x": 36.5} 
        }

        # --- 全20チーム個別座標テーブル（PM指示：上下に0.5%ずつの遊びを追加） ---
        # Yuyaさんの最新座標をベースに y-0.5, h+1.0 しています
        self.team_coords = [
            {"y": 23.5, "h": 4.0}, # #1
            {"y": 33, "h": 4.0}, # #2
            {"y": 41, "h": 4.0}, # #3
            {"y": 47.5, "h": 4.0}, # #4
            {"y": 54, "h": 4.0}, # #5
            {"y": 60.5, "h": 4.0}, # #6
            {"y": 66.5, "h": 4.0}, # #7
            {"y": 73, "h": 4.0}, # #8
            {"y": 80, "h": 4.0}, # #9
            {"y": 15, "h": 4.0}, # #10
            {"y": 21.5, "h": 4.0}, # #11
            {"y": 28, "h": 4.0}, # #12
            {"y": 34.5, "h": 4.0}, # #13
            {"y": 41, "h": 4.0}, # #14
            {"y": 47.5, "h": 4.0}, # #15
            {"y": 53.5, "h": 4.0}, # #16
            {"y": 59.5, "h": 4.0}, # #17
            {"y": 65.5, "h": 4.0}, # #18
            {"y": 71.5, "h": 4.0}, # #19
            {"y": 77.5, "h": 4.0}, # #20
        ]

    def get_all_fragments(self, image_path):
        img = cv2.imread(image_path)
        img = self._resize_with_aspect_ratio(img, self.target_w, self.target_h)
        h, w = img.shape[:2]
        all_fragments = []

        for i, coord in enumerate(self.team_coords):
            is_right = (i >= 9)
            col_x_base = self.x_right_base if is_right else self.x_left_base
            y1, y2 = int(coord["y"] * h / 100), int((coord["y"] + coord["h"]) * h / 100)
            
            fragments = {}
            for field, f_info in self.fields.items():
                x1 = int((col_x_base + f_info["offset_x"]) * w / 100)
                x2 = int((col_x_base + f_info["offset_x"] + f_info["width"]) * w / 100)
                crop = img[y1:y2, x1:x2]
                fragments[field] = self._preprocess_for_ocr(crop)
            all_fragments.append(fragments)
        return all_fragments

    def _preprocess_for_ocr(self, crop):
        """
        【逆転の発想：完全無加工】
        人間が加工するのをやめ、Google Vision APIに生の色情報を渡す。
        これが最も精度が出るパターンです。
        """
        # BGR(OpenCV)をRGB(API用)に変換するだけ
        rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        return rgb_crop

    def _resize_with_aspect_ratio(self, img, target_w, target_h):
        h_orig, w_orig = img.shape[:2]
        scale = min(target_w / w_orig, target_h / h_orig)
        new_w, new_h = int(w_orig * scale), int(h_orig * scale)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        canvas[(target_h-new_h)//2:(target_h-new_h)//2+new_h, (target_w-new_w)//2:(target_w-new_w)//2+new_w] = resized
        return canvas