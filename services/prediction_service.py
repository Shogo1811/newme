"""
予測処理のサービス層（ビジネスロジック統合）
"""
from dataclasses import dataclass
from typing import Dict, Optional
import logging

from models.data_processor import load_and_preprocess_data
from models.predictor import (
    train_and_evaluate_model,
    train_full_model,
    aggregate_by_ward,
    aggregate_by_era,
    predict_single_property
)
from models.visualizer import create_scatter_plot, create_yearly_trend_plot

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """予測結果を格納するデータクラス"""
    rmse: float
    r2: float
    scatter_plot_path: str
    trend_plot_path: str
    predictions_by_ward: Dict[str, int]
    actual_prices_by_ward: Dict[str, int]
    era_predictions: Dict[str, Dict[str, int]]
    model: any = None  # 学習済みモデル（個別予測用）
    feature_columns: list = None  # 特徴量カラム（個別予測用）


def process_and_predict(file_path: str) -> PredictionResult:
    """
    CSV読み込み～予測～可視化の一連処理を実行

    Args:
        file_path (str): CSVファイルのパス

    Returns:
        PredictionResult: 予測結果を含むデータクラス

    Raises:
        FileNotFoundError: ファイルが存在しない
        KeyError: 必要なカラムが不足
        ValueError: データの形式が不正
    """
    logger.info(f"予測処理開始: {file_path}")

    try:
        # 1. データ読み込み・前処理
        df_original, X, y = load_and_preprocess_data(file_path)

        # 2. モデル学習・評価
        model, rmse, r2, y_test, y_pred = train_and_evaluate_model(X, y)

        # 3. 散布図生成
        scatter_plot_path = create_scatter_plot(y_test, y_pred)

        # 4. 全データで再学習
        model_full = train_full_model(X, y)
        predictions_all = model_full.predict(X)

        # 5. 区ごとの集計
        predictions_by_ward, actual_prices_by_ward = aggregate_by_ward(
            df_original, predictions_all
        )

        # 6. 築年帯ごとの集計
        era_predictions = aggregate_by_era(df_original, predictions_all)

        # 7. 年次推移グラフ生成
        trend_plot_path = create_yearly_trend_plot(df_original)

        # 8. 結果をデータクラスに格納
        result = PredictionResult(
            rmse=rmse,
            r2=r2,
            scatter_plot_path=scatter_plot_path,
            trend_plot_path=trend_plot_path,
            predictions_by_ward=predictions_by_ward,
            actual_prices_by_ward=actual_prices_by_ward,
            era_predictions=era_predictions,
            model=model_full,  # 個別予測用にモデルを保存
            feature_columns=list(X.columns)  # 特徴量カラムを保存
        )

        logger.info("予測処理完了")
        return result

    except Exception as e:
        logger.error(f"予測処理中にエラーが発生: {e}", exc_info=True)
        raise


def predict_from_input(
    area: float,
    age: int,
    distance: float,
    ward: str
) -> Optional[float]:
    """
    ユーザー入力から価格を予測

    注意: この関数を使用する前に、process_and_predict()を実行して
    モデルと特徴量カラムをセッションに保存しておく必要があります。

    Args:
        area (float): 面積（㎡）
        age (int): 築年数（年）
        distance (float): 最寄駅距離（分）
        ward (str): 市区町村名

    Returns:
        Optional[float]: 予測価格（円）、モデルが存在しない場合はNone

    Raises:
        ValueError: 入力値が不正
    """
    # バリデーション
    if area <= 0:
        raise ValueError("面積は0より大きい値を入力してください")
    if age < 0:
        raise ValueError("築年数は0以上の値を入力してください")
    if distance < 0:
        raise ValueError("最寄駅距離は0以上の値を入力してください")
    if not ward:
        raise ValueError("市区町村名を選択してください")

    logger.info(
        f"個別予測リクエスト: 区={ward}, 面積={area}㎡, "
        f"築{age}年, 駅徒歩{distance}分"
    )

    # この関数は、セッションからモデルと特徴量を取得する必要があるため、
    # 実際の予測処理はapp.pyで実装します
    # ここではバリデーションのみ行います
    return None
