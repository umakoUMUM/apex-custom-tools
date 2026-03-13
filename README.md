# Apexカスタムリザルト集計ツール

Apex Legendsのカスタムマッチで、スクリーンショットから戦績（順位・チーム名・キル数）を読み取って、スプレッドシートに書き込むツールです。

## ⚠️ 大事な注意点
- スクリーンショットは必ず **1920×1080** の解像度で撮影してください。
- それ以外の解像度だと、文字を読み取る場所がズレて正しく動きません。

## 📊 セルの色について
- **オレンジ色（補正）**: ツールが自動で数値を直した箇所です。
- **赤色（異常）**: 読み取りミスが疑われる箇所です。手動で直してください。

## 🛠️ 準備（初めて使う時）

### 1. Pythonの仮想環境を作る
ターミナル（PowerShell）で以下を一行ずつ実行してください。
   python -m venv .venv
   .\.venv\Scripts\activate

※エラーが出る場合は以下を実行してから再度 activate してください。
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

### 2. ライブラリを入れる
   pip install -r requirements.txt


### 3. ファイルの配置
- **.env**: ルート（main.pyと同じ場所）に作成し、以下のように記入します。
  SPREADSHEET_ID=ここにスプレッドシートのIDを貼り付け
- **credentials.json**: Google Cloudで作成したキーを、この名前でルートに置きます。
- **config.yaml**: チーム数などを確認します。

### 4. Google Cloud (GCP) の設定
- 以下の3つのAPIを「有効」にします。
  1. Cloud Vision API / 2. Google Sheets API / 3. Google Drive API
- サービスアカウントを作成し、そのメールアドレスをスプレッドシートの「共有」から「編集者」で追加してください。

## 📝 使い方
1. screenshots フォルダに画像を入れます。
2. プログラムを実行します。
   python main.py

3. 終わると画像は自動的に processed フォルダに移動します。