"""
機械学習モデルの学習・予測モジュール
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from typing import Tuple, Dict
import logging

from config import config

logger = logging.getLogger(__name__)


def train_and_evaluate_model(
    X: pd.DataFrame,
    y: pd.Series
) -> Tuple[RandomForestRegressor, float, float, np.ndarray, np.ndarray]:
    """
    モデルを学習し、評価指標と予測値を返す

    Args:
        X (pd.DataFrame): 特徴量
        y (pd.Series): 目的変数

    Returns:
        Tuple[RandomForestRegressor, float, float, np.ndarray, np.ndarray]:
            (学習済みモデル, RMSE, R²スコア, テストデータの実測値, 予測値)
    """
    # データ分割
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=config.TEST_SIZE,
        random_state=config.RANDOM_STATE
    )

    logger.info(f"データ分割: 学習{len(X_train)}件, テスト{len(X_test)}件")

    # モデル学習
    model = RandomForestRegressor(
        random_state=config.RANDOM_STATE,
        n_estimators=config.RF_N_ESTIMATORS,
        max_depth=config.RF_MAX_DEPTH,
        n_jobs=config.RF_N_JOBS
    )

    logger.info("モデル学習開始...")
    model.fit(X_train, y_train)
    logger.info("モデル学習完了")

    # 予測
    y_pred = model.predict(X_test)
    y_pred = np.round(y_pred, 2)

    # 評価指標計算
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    logger.info(f"評価結果 - RMSE: {rmse:,.2f}, R²: {r2:.4f}")

    return model, rmse, r2, y_test.values, y_pred


def train_full_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """
    全データでモデルを再学習

    Args:
        X (pd.DataFrame): 特徴量（全データ）
        y (pd.Series): 目的変数（全データ）

    Returns:
        RandomForestRegressor: 学習済みモデル
    """
    model = RandomForestRegressor(
        random_state=config.RANDOM_STATE,
        n_estimators=config.RF_N_ESTIMATORS,
        max_depth=config.RF_MAX_DEPTH,
        n_jobs=config.RF_N_JOBS
    )

    logger.info("全データでモデル再学習開始...")
    model.fit(X, y)
    logger.info("全データでモデル再学習完了")

    return model


def aggregate_by_ward(
    df_original: pd.DataFrame,
    predictions: np.ndarray
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    区ごとの予測価格と実際価格を集計

    Args:
        df_original (pd.DataFrame): 元データ
        predictions (np.ndarray): 予測値

    Returns:
        Tuple[Dict[str, int], Dict[str, int]]:
            (区ごとの予測価格辞書, 区ごとの実際価格辞書)
    """
    df = df_original.copy()
    df["Predicted Price"] = predictions

    # 区ごとの予測価格の平均
    ward_predictions = (
        df.groupby("市区町村名")["Predicted Price"]
        .mean()
        .round()
        .astype(int)
        .to_dict()
    )

    # 区ごとの実際価格の平均
    ward_actuals = (
        df.groupby("市区町村名")["取引価格（総額）"]
        .mean()
        .round()
        .astype(int)
        .to_dict()
    )

    logger.info(f"区ごとの集計完了: {len(ward_predictions)}区")

    return ward_predictions, ward_actuals


def aggregate_by_era(
    df_original: pd.DataFrame,
    predictions: np.ndarray
) -> Dict[str, Dict[str, int]]:
    """
    築年帯ごとの予測価格を集計

    Args:
        df_original (pd.DataFrame): 元データ
        predictions (np.ndarray): 予測値

    Returns:
        Dict[str, Dict[str, int]]: 区×築年帯の予測価格辞書
    """
    df = df_original.copy()
    df["Predicted Price"] = predictions

    # 建築年の処理
    df["建築年"] = pd.to_numeric(
        df["建築年"].str.replace("年", ""),
        errors="coerce"
    )

    # 築年帯の分類
    df["築年帯"] = pd.cut(
        config.CURRENT_YEAR - df["建築年"],
        bins=config.AGE_BINS,
        labels=config.AGE_LABELS
    )

    # 区×築年帯でグループ化
    by_ward_and_era = (
        df.groupby(["市区町村名", df["築年帯"]])["Predicted Price"]
        .mean()
        .unstack()
        .fillna(0)
        .round()
        .astype(int)
        .to_dict(orient="index")
    )

    logger.info(f"築年帯別集計完了: {len(by_ward_and_era)}区")

    return by_ward_and_era


def get_feature_importance(
    model: RandomForestRegressor,
    feature_names: list
) -> pd.DataFrame:
    """
    特徴量の重要度を取得

    Args:
        model (RandomForestRegressor): 学習済みモデル
        feature_names (list): 特徴量名のリスト

    Returns:
        pd.DataFrame: 特徴量の重要度（降順ソート）
    """
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    logger.info(f"特徴量重要度トップ5:\n{importance_df.head()}")

    return importance_df
