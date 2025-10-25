# 東京23区マンション価格予測システム（リファクタリング版）

機械学習（Random Forest）を使用して、東京23区のマンション価格を予測するWebアプリケーションです。

## 主要な改善点

### リファクタリング前の問題点を解決
- ✅ **グローバル変数の排除**: Flaskセッションで状態管理
- ✅ **エラーハンドリングの実装**: 全ての処理に適切な例外処理
- ✅ **セキュリティ対策**: ファイルアップロードのバリデーション、サニタイズ
- ✅ **関数の分割**: 巨大関数を責務ごとに分割（単一責任原則）
- ✅ **設定の外部化**: config.pyで一元管理
- ✅ **ロギング実装**: 本番環境対応のログ出力
- ✅ **テストコード追加**: 単体テスト・統合テスト
- ✅ **型ヒントの統一**: 全関数に型ヒント付与

## プロジェクト構造

```
newme/
├── app_new.py                      # Flaskアプリケーション（リファクタリング版）
├── app.py                          # Flaskアプリケーション（旧版）
├── model_utils.py                  # 機械学習処理（旧版）
├── config.py                       # 設定ファイル
├── requirements.txt                # 依存パッケージ
│
├── models/                         # 機械学習モデル
│   ├── __init__.py
│   ├── data_processor.py          # データ前処理
│   ├── predictor.py               # モデル学習・予測
│   └── visualizer.py              # グラフ生成
│
├── services/                       # ビジネスロジック層
│   ├── __init__.py
│   └── prediction_service.py      # 予測サービス統合
│
├── utils/                          # ユーティリティ
│   ├── __init__.py
│   ├── font_config.py             # フォント設定
│   └── file_handler.py            # ファイル処理
│
├── templates/                      # HTMLテンプレート
│   ├── base.html
│   ├── upload.html
│   ├── result_overview.html
│   ├── result_by_ward.html
│   ├── result_by_era.html
│   └── result_graphs.html
│
├── static/                         # 静的ファイル
│   ├── result.png                 # 散布図
│   └── yearly_trend.png           # 年次推移グラフ
│
├── input/                          # アップロードCSV
├── logs/                           # ログファイル
└── tests/                          # テストコード
    ├── __init__.py
    ├── test_app.py
    ├── test_data_processor.py
    └── test_file_handler.py
```

## セットアップ

### 1. 仮想環境の作成・有効化
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### 2. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定（オプション）
```bash
export FLASK_DEBUG=False          # 本番環境ではFalse
export SECRET_KEY=your-secret-key  # セッション用シークレットキー
export PORT=5002                   # ポート番号
```

## 使用方法

### 旧版の実行
```bash
python app.py
```

### リファクタリング版の実行
```bash
python app_new.py
```

ブラウザで `http://localhost:5002` にアクセス

### テストの実行
```bash
# 全テスト実行
python -m unittest discover tests

# 個別テスト実行
python -m unittest tests.test_data_processor
python -m unittest tests.test_file_handler
python -m unittest tests.test_app
```

## 機能

### 1. CSVファイルアップロード
- 国土交通省「不動産取引価格情報」形式のCSVをアップロード
- ファイル形式検証（CSV以外は拒否）
- ファイルサイズ制限（50MB）
- ファイル名のサニタイズ（セキュリティ対策）

### 2. 機械学習による価格予測
- **アルゴリズム**: Random Forest Regressor
- **特徴量**:
  - 面積（㎡）
  - 最寄駅距離（分）
  - 建築年
  - 取引年
  - 市区町村名（ダミー変数）
  - 築年帯（ダミー変数）
- **評価指標**:
  - RMSE（平均二乗誤差の平方根）
  - R²スコア（決定係数）

### 3. 可視化
- **散布図**: 実際価格 vs 予測価格
- **年次推移グラフ**: 年度ごとの平均価格推移
- **区別集計**: 区ごとの予測・実際価格比較
- **築年帯別集計**: 区×築年帯の価格マトリクス

## 設定

`config.py`で以下の設定が可能:

### Flask設定
- `SECRET_KEY`: セッション用シークレットキー
- `DEBUG`: デバッグモード
- `PORT`: ポート番号

### ファイル設定
- `MAX_FILE_SIZE`: 最大ファイルサイズ（デフォルト: 50MB）
- `ALLOWED_EXTENSIONS`: 許可する拡張子（デフォルト: csv）
- `CSV_ENCODING`: CSVエンコーディング（デフォルト: cp932）

### 機械学習設定
- `TEST_SIZE`: テストデータ比率（デフォルト: 0.2）
- `RANDOM_STATE`: 乱数シード（デフォルト: 42）
- `RF_N_ESTIMATORS`: Random Forestの木の数（デフォルト: 100）
- `RF_N_JOBS`: 並列処理数（デフォルト: -1 = 全コア使用）

### グラフ設定
- `PLOT_DPI`: グラフ解像度（デフォルト: 300）
- `PRICE_FILTER_THRESHOLD`: 外れ値除外閾値（デフォルト: 2.5億円）

## エラーハンドリング

リファクタリング版では以下のエラーに対応:

- **ファイル未選択**: エラーメッセージ表示
- **不正なファイル形式**: CSVのみ許可
- **ファイルサイズ超過**: 50MB制限
- **CSV形式不正**: 必須カラムチェック
- **データ処理エラー**: 適切なエラーメッセージ

## ログ

`logs/app.log`に以下の情報を記録:

- アプリケーション起動/停止
- ファイルアップロード
- 予測処理の開始/完了
- エラー情報（スタックトレース含む）

ログファイルは10MBでローテーション（最大10ファイル保持）

## セキュリティ

### 実装済み対策
- ファイル名のサニタイズ（`secure_filename`使用）
- ファイル拡張子検証
- ファイルサイズ制限
- セッション管理（`SECRET_KEY`使用）

### 本番環境での推奨事項
- `DEBUG=False`に設定
- `SECRET_KEY`を強固なランダム文字列に変更
- HTTPS通信の使用
- Gunicorn + Nginx構成
- ファイアウォール設定

## パフォーマンス

### 最適化済み項目
- CSVファイルの1回のみ読み込み（重複排除）
- Random Forestの並列処理（`n_jobs=-1`）
- 古いファイルの自動クリーンアップ

### 推定処理時間
- データ読み込み: 1～3秒
- モデル学習: 5～10秒（1万件の場合）
- グラフ生成: 2～4秒
- **合計**: 約10～20秒

## トラブルシューティング

### フォント関連エラー
日本語が文字化けする場合、以下のフォントをインストール:

- **macOS**: ヒラギノ角ゴシック（通常プリインストール済み）
- **Windows**: Yu Gothic / MS Gothic（通常プリインストール済み）
- **Linux**: `sudo apt-get install fonts-noto-cjk`

### メモリ不足エラー
大量データ処理時にメモリ不足が発生する場合:

1. `config.py`で`RF_MAX_DEPTH`を設定（例: 20）
2. `RF_N_ESTIMATORS`を減らす（例: 50）
3. データを分割して処理

### ポート使用中エラー
```bash
# 別のポートを指定
export PORT=5003
python app_new.py
```

## ライセンス

教育目的のプロジェクトです。

## 変更履歴

### v2.0.0（リファクタリング版）- 2025-10-25
- グローバル変数をFlaskセッションに移行
- エラーハンドリングの全面実装
- セキュリティ対策（ファイルバリデーション、サニタイズ）
- モジュール分割（models, services, utils）
- 設定の外部化（config.py）
- ロギング実装
- テストコード追加
- 型ヒントの統一

### v1.0.0（初版）- 2024-XX-XX
- 基本機能実装
