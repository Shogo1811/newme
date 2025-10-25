# マイグレーションガイド

旧版（`app.py` + `model_utils.py`）からリファクタリング版（`app_new.py` + モジュール構成）への移行ガイドです。

## 移行手順

### Step 1: バックアップの作成
```bash
# 現在の動作環境をバックアップ
cp -r . ../newme_backup
```

### Step 2: 新しい依存パッケージのインストール
```bash
pip install -r requirements.txt
```

### Step 3: リファクタリング版の動作確認
```bash
# テスト実行
python -m unittest discover tests

# アプリケーション起動
python app_new.py
```

### Step 4: テストCSVでの動作確認
1. ブラウザで `http://localhost:5002` にアクセス
2. 既存のテストCSVファイルをアップロード
3. 予測結果が正常に表示されることを確認

### Step 5: 本番環境への切り替え

#### オプション1: 段階的移行（推奨）
```bash
# 旧版を別ポートで起動
PORT=5001 python app.py &

# 新版を起動
PORT=5002 python app_new.py &

# 両方を並行稼働させてテスト
```

#### オプション2: 完全移行
```bash
# 旧版をバックアップとして保存
mv app.py app_old.py
mv model_utils.py model_utils_old.py

# 新版をメインとして使用
mv app_new.py app.py
```

## 主要な変更点

### 1. グローバル変数 → Flaskセッション

**旧版:**
```python
# グローバル変数
rmse = None
r2 = None

@app.route("/result_overview")
def result_overview():
    return render_template("result_overview.html", rmse=rmse, r2=r2)
```

**新版:**
```python
# セッションで管理
session['rmse'] = result.rmse
session['r2'] = result.r2

@app.route("/result_overview")
def result_overview():
    rmse = session.get('rmse')
    r2 = session.get('r2')
    return render_template("result_overview.html", rmse=rmse, r2=r2)
```

### 2. 巨大関数の分割

**旧版:**
```python
# 104行の巨大関数
def process_and_predict(file_path: str):
    # フォント設定
    # CSV読み込み
    # データ前処理
    # モデル学習
    # グラフ生成
    # 集計
    # ...
```

**新版:**
```python
# 責務ごとに分割
def load_and_preprocess_data(file_path: str):
    # データ読み込み・前処理のみ

def train_and_evaluate_model(X, y):
    # モデル学習・評価のみ

def create_scatter_plot(y_test, y_pred):
    # グラフ生成のみ

# サービス層で統合
def process_and_predict(file_path: str):
    df_original, X, y = load_and_preprocess_data(file_path)
    model, rmse, r2, y_test, y_pred = train_and_evaluate_model(X, y)
    create_scatter_plot(y_test, y_pred)
    # ...
```

### 3. エラーハンドリング

**旧版:**
```python
# エラーハンドリングなし
if file:
    file.save(filepath)
    rmse, r2, ... = process_and_predict(filepath)
```

**新版:**
```python
# 全ての処理に例外処理
try:
    success, filepath, error = save_uploaded_file(file)
    if not success:
        flash(error, "error")
        return redirect(url_for("upload_file"))

    result = process_and_predict(filepath)
except KeyError as e:
    flash(f"CSV形式が不正です: {e}", "error")
    return redirect(url_for("upload_file"))
except Exception as e:
    flash(f"エラー: {e}", "error")
    return redirect(url_for("upload_file"))
```

### 4. 設定の外部化

**旧版:**
```python
# ハードコード
df = pd.read_csv(file_path, encoding="cp932")
model = RandomForestRegressor(random_state=42)
app.run(debug=True, port=5002)
```

**新版:**
```python
# config.pyで管理
from config import config

df = pd.read_csv(file_path, encoding=config.CSV_ENCODING)
model = RandomForestRegressor(
    random_state=config.RANDOM_STATE,
    n_estimators=config.RF_N_ESTIMATORS
)
app.run(debug=config.DEBUG, port=config.PORT)
```

## インポート文の変更

### 旧版のインポート
```python
from model_utils import process_and_predict
```

### 新版のインポート
```python
from services.prediction_service import process_and_predict
from models.data_processor import load_and_preprocess_data
from models.predictor import train_and_evaluate_model
from models.visualizer import create_scatter_plot
from utils.file_handler import validate_uploaded_file, save_uploaded_file
from config import config
```

## 互換性

### 後方互換性のある変更
- テンプレートファイル（templates/）はそのまま使用可能
- CSVファイル形式は変更なし
- 予測アルゴリズム（Random Forest）は同一
- グラフの見た目は基本的に同じ

### 後方互換性のない変更
- `model_utils.py`の関数を直接呼ぶコードは動作しない
- グローバル変数に依存するコードは動作しない
- 環境変数の設定方法が変更

## ロールバック手順

問題が発生した場合のロールバック:

```bash
# バックアップから復元
cp ../newme_backup/app.py ./
cp ../newme_backup/model_utils.py ./

# 旧版で再起動
python app.py
```

## 確認項目

移行後、以下を確認してください:

- [ ] CSVファイルのアップロードが正常に動作する
- [ ] 予測結果（RMSE、R²スコア）が表示される
- [ ] 散布図が生成される
- [ ] 年次推移グラフが生成される
- [ ] 区ごとの予測ページが表示される
- [ ] 築年帯ごとの予測ページが表示される
- [ ] エラー発生時に適切なメッセージが表示される
- [ ] ログファイルが生成される
- [ ] 日本語フォントが正しく表示される

## サポート

移行中に問題が発生した場合:

1. ログファイル（`logs/app.log`）を確認
2. テストを実行して問題箇所を特定
3. 必要に応じてバックアップからロールバック

## 追加機能

新版では以下の機能が追加されています:

### ファイルクリーンアップ
古いアップロードファイルを自動削除（最大10ファイル保持）

### セッション管理
複数ユーザーの同時利用に対応（グローバル変数を使用しない）

### セキュリティ強化
- ファイル名のサニタイズ
- 拡張子チェック
- ファイルサイズ制限

### ロギング
全ての処理をログファイルに記録

### テストコード
自動テストによる品質保証
