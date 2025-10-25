"""
データ読み込み・前処理モジュール
"""
import pandas as pd
import numpy as np
from typing import Union, Tuple
import logging

from config import config

logger = logging.getLogger(__name__)


def parse_distance(distance: Union[str, int, float]) -> Union[int, float]:
    """
    最寄駅距離データを数値（分）に正規化

    Args:
        distance (str | int | float): 距離データ
            - "5分" → 5
            - "1H30分" → 90 (1時間30分)
            - "5～10分" → 7.5 (平均値)

    Returns:
        int | float: 正規化された距離（分）
    """
    if isinstance(distance, str):
        # 時間表記（例: "1H30分" → 90分）
        if "H" in distance:
            parts = distance.replace("分", "").split("H")
            hours = int(parts[0]) * 60
            minutes = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            return hours + minutes

        # 範囲表記（例: "5～10分" → 7.5分）
        elif "～" in distance:
            parts = distance.replace("分", "").split("～")
            return (int(parts[0]) + int(parts[1])) / 2

        # 通常の分表記（例: "5分" → 5）
        elif "分" in distance:
            return int(distance.replace("分", ""))

    # すでに数値の場合はそのまま返す
    return distance


def load_csv_data(file_path: str) -> pd.DataFrame:
    """
    CSVファイルを読み込む

    Args:
        file_path (str): CSVファイルのパス

    Returns:
        pd.DataFrame: 読み込んだデータフレーム

    Raises:
        FileNotFoundError: ファイルが存在しない
        pd.errors.EmptyDataError: ファイルが空
        UnicodeDecodeError: エンコーディングエラー
    """
    try:
        df = pd.read_csv(file_path, encoding=config.CSV_ENCODING)
        logger.info(f"CSVファイル読み込み成功: {file_path} ({len(df)}行)")
        return df
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"ファイルが空です: {file_path}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"エンコーディングエラー: {file_path} - {e}")
        raise


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    カラム名のクリーニング（BOM削除）

    Args:
        df (pd.DataFrame): データフレーム

    Returns:
        pd.DataFrame: クリーニング後のデータフレーム
    """
    df = df.copy()
    df.columns = df.columns.str.replace("\ufeff", "")
    return df


def extract_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    必要なカラムを抽出

    Args:
        df (pd.DataFrame): データフレーム

    Returns:
        pd.DataFrame: 必要なカラムのみを含むデータフレーム

    Raises:
        KeyError: 必要なカラムが存在しない
    """
    required_columns = [
        "取引価格（総額）",
        "面積（㎡）",
        "最寄駅：距離（分）",
        "建築年",
        "市区町村名",
        "取引時期"
    ]

    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        error_msg = f"必要なカラムが不足しています: {missing_columns}"
        logger.error(error_msg)
        raise KeyError(error_msg)

    return df[required_columns].copy()


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    データの前処理

    Args:
        df (pd.DataFrame): 生データ

    Returns:
        pd.DataFrame: 前処理後のデータ
    """
    df = df.copy()

    # 建築年の処理（"年"を削除して数値化）
    df["建築年"] = pd.to_numeric(
        df["建築年"].str.replace("年", ""),
        errors="coerce"
    )

    # 最寄駅距離の正規化
    df["最寄駅：距離（分）"] = df["最寄駅：距離（分）"].apply(parse_distance)

    # 取引年の抽出
    df["取引年"] = df["取引時期"].str.extract(r"(\d{4})").astype(float)

    # 築年帯の分類
    df["築年帯"] = pd.cut(
        config.CURRENT_YEAR - df["建築年"],
        bins=config.AGE_BINS,
        labels=config.AGE_LABELS
    )

    # 欠損値削除
    rows_before = len(df)
    df = df.dropna()
    rows_after = len(df)

    if rows_before > rows_after:
        logger.info(f"欠損値を含む行を削除: {rows_before - rows_after}行")

    return df


def create_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    特徴量を作成し、X, yに分割

    Args:
        df (pd.DataFrame): 前処理済みデータ

    Returns:
        Tuple[pd.DataFrame, pd.Series]: (特徴量X, 目的変数y)
    """
    df = df.copy()

    # ダミー変数化（市区町村名、築年帯）
    df = pd.get_dummies(
        df.drop(columns=["取引時期"]),
        columns=["市区町村名", "築年帯"],
        drop_first=True
    )

    # 特徴量と目的変数に分割
    X = df.drop("取引価格（総額）", axis=1)
    y = df["取引価格（総額）"]

    logger.info(f"特徴量作成完了: {X.shape[1]}個の特徴量")

    return X, y


def load_and_preprocess_data(file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    CSVファイルを読み込み、前処理を実行

    Args:
        file_path (str): CSVファイルのパス

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
            (元データ, 特徴量X, 目的変数y)

    Raises:
        FileNotFoundError: ファイルが存在しない
        KeyError: 必要なカラムが不足
        ValueError: データの形式が不正
    """
    # CSV読み込み
    df_original = load_csv_data(file_path)

    # カラム名クリーニング
    df_original = clean_column_names(df_original)

    # 必要なカラム抽出
    df = extract_required_columns(df_original)

    # データ前処理
    df = preprocess_data(df)

    # 元データも同じインデックスに絞る（後で使用するため）
    df_original = df_original.loc[df.index]

    # 特徴量作成
    X, y = create_features(df)

    logger.info(f"データ前処理完了: {len(df)}サンプル")

    return df_original, X, y
