"""
アプリケーション設定ファイル
環境変数または定数で設定を管理
"""
import os
from dataclasses import dataclass
from typing import Set


@dataclass
class Config:
    """アプリケーション設定クラス"""

    # Flask設定
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-please-change-in-production')
    DEBUG: bool = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    PORT: int = int(os.environ.get('PORT', 5002))

    # ファイル設定
    UPLOAD_FOLDER: str = 'input'
    STATIC_FOLDER: str = 'static'
    TEMPLATE_FOLDER: str = 'templates'
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: Set[str] = frozenset({'csv'})
    CSV_ENCODING: str = 'cp932'

    # 機械学習設定
    TEST_SIZE: float = 0.2
    RANDOM_STATE: int = 42
    RF_N_ESTIMATORS: int = 100
    RF_MAX_DEPTH: int = None  # Noneは制限なし
    RF_N_JOBS: int = -1  # 全CPUコア使用

    # データ処理設定
    CURRENT_YEAR: int = 2025
    AGE_BINS: list = None  # __post_init__で初期化
    AGE_LABELS: list = None  # __post_init__で初期化

    # グラフ設定
    PLOT_DPI: int = 300
    SCATTER_PLOT_PATH: str = 'static/result.png'
    TREND_PLOT_PATH: str = 'static/yearly_trend.png'
    PRICE_FILTER_THRESHOLD: int = 250_000_000  # 2.5億円
    GRAPH_MAX_PRICE: int = 200_000_000  # 2億円
    GRAPH_TICK_INTERVAL: int = 50_000_000  # 5千万円
    SCATTER_FIGURE_SIZE: tuple = (8, 8)
    TREND_FIGURE_SIZE: tuple = (10, 6)

    # ログ設定
    LOG_FILE: str = 'logs/app.log'
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 10
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    def __post_init__(self):
        """初期化後の処理"""
        # リスト型の設定値を初期化
        if self.AGE_BINS is None:
            object.__setattr__(self, 'AGE_BINS', [0, 10, 20, 999])
        if self.AGE_LABELS is None:
            object.__setattr__(self, 'AGE_LABELS', ["築10年未満", "築10～20年", "築20年以上"])


# グローバル設定インスタンス
config = Config()
