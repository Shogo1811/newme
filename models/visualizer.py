"""
グラフ可視化モジュール
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # GUIを使わないバックエンド
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import Optional
import logging

from config import config
from utils.font_config import setup_japanese_font

logger = logging.getLogger(__name__)


def create_scatter_plot(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    save_path: Optional[str] = None
) -> str:
    """
    実際価格 vs 予測価格の散布図を生成

    Args:
        y_test (np.ndarray): テストデータの実測値
        y_pred (np.ndarray): 予測値
        save_path (str, optional): 保存先パス

    Returns:
        str: 保存したファイルパス
    """
    if save_path is None:
        save_path = config.SCATTER_PLOT_PATH

    # 日本語フォント設定
    setup_japanese_font()

    # データフレーム作成
    comparison = pd.DataFrame({
        "Actual Price": y_test,
        "Predicted Price": y_pred.astype(int)
    })

    # 価格フィルタ（外れ値除外）
    filtered = comparison[
        (comparison["Actual Price"] < config.PRICE_FILTER_THRESHOLD) &
        (comparison["Predicted Price"] < config.PRICE_FILTER_THRESHOLD)
    ]

    logger.info(f"散布図データ点数: {len(filtered)}件（元: {len(comparison)}件）")

    # グラフ作成
    plt.figure(figsize=config.SCATTER_FIGURE_SIZE)
    ax = plt.gca()

    # 軸設定
    ticks = np.arange(0, config.GRAPH_MAX_PRICE + 1, config.GRAPH_TICK_INTERVAL)
    ax.set_xlim(0, config.GRAPH_MAX_PRICE)
    ax.set_ylim(0, config.GRAPH_MAX_PRICE)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)

    # 軸ラベルのフォーマット（百万円単位）
    ax.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda val, _: f"{int(val / 1e6):,}")
    )
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda val, _: f"{int(val / 1e6):,}")
    )

    # グリッド
    ax.grid(which="major", linestyle="--", linewidth=0.5)

    # 散布図
    plt.scatter(
        filtered["Actual Price"],
        filtered["Predicted Price"],
        color="orange",
        alpha=0.7,
        s=30
    )

    # 理想線（y=x）
    plt.plot(
        [0, config.GRAPH_MAX_PRICE],
        [0, config.GRAPH_MAX_PRICE],
        '--r',
        linewidth=2,
        label="理想線 (y=x)"
    )

    # ラベル・タイトル
    plt.xlabel("実際の価格 (百万円)", fontsize=12)
    plt.ylabel("予測価格 (百万円)", fontsize=12)
    plt.title("実際の価格 vs 予測価格の比較", fontsize=14, fontweight='bold')
    plt.legend()

    # 保存
    plt.tight_layout()
    plt.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches='tight')
    plt.close()

    logger.info(f"散布図保存完了: {save_path}")

    return save_path


def create_yearly_trend_plot(
    df_original: pd.DataFrame,
    save_path: Optional[str] = None
) -> str:
    """
    年次別の平均価格推移グラフを生成

    Args:
        df_original (pd.DataFrame): 元データ
        save_path (str, optional): 保存先パス

    Returns:
        str: 保存したファイルパス
    """
    if save_path is None:
        save_path = config.TREND_PLOT_PATH

    # 日本語フォント設定
    setup_japanese_font()

    df = df_original.copy()

    # 取引年を抽出
    df["取引年"] = df["取引時期"].str.extract(r"(\d{4})").astype(float)

    # 年度別平均価格
    yearly_price = (
        df.groupby("取引年")["取引価格（総額）"]
        .mean()
        .dropna()
        .sort_index()
    )

    logger.info(f"年次推移データ: {len(yearly_price)}年分")

    # グラフ作成
    plt.figure(figsize=config.TREND_FIGURE_SIZE)

    yearly_price.plot(
        marker="o",
        linewidth=2,
        markersize=6,
        color='#3498db'
    )

    plt.title("年度ごとの平均取引価格推移", fontsize=14, fontweight='bold')
    plt.xlabel("取引年", fontsize=12)
    plt.ylabel("平均価格（円）", fontsize=12)
    plt.grid(True, alpha=0.3)

    # Y軸のフォーマット（百万円単位）
    ax = plt.gca()
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda val, _: f"{int(val / 1e6):,}M")
    )

    # 保存
    plt.tight_layout()
    plt.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches='tight')
    plt.close()

    logger.info(f"年次推移グラフ保存完了: {save_path}")

    return save_path


def create_ward_comparison_plot(
    ward_predictions: dict,
    ward_actuals: dict,
    save_path: str = "static/ward_comparison.png"
) -> str:
    """
    区ごとの予測価格と実際価格の比較棒グラフを生成（オプション機能）

    Args:
        ward_predictions (dict): 区ごとの予測価格
        ward_actuals (dict): 区ごとの実際価格
        save_path (str): 保存先パス

    Returns:
        str: 保存したファイルパス
    """
    # 日本語フォント設定
    setup_japanese_font()

    # データフレーム作成
    df = pd.DataFrame({
        '予測価格': ward_predictions,
        '実際価格': ward_actuals
    }).sort_values('実際価格', ascending=False)

    # 百万円単位に変換
    df = df / 1e6

    # グラフ作成
    fig, ax = plt.subplots(figsize=(12, 8))

    x = np.arange(len(df))
    width = 0.35

    ax.bar(x - width/2, df['実際価格'], width, label='実際価格', color='#3498db')
    ax.bar(x + width/2, df['予測価格'], width, label='予測価格', color='#e74c3c')

    ax.set_xlabel('区', fontsize=12)
    ax.set_ylabel('価格 (百万円)', fontsize=12)
    ax.set_title('区ごとの実際価格と予測価格の比較', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(df.index, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(save_path, dpi=config.PLOT_DPI, bbox_inches='tight')
    plt.close()

    logger.info(f"区別比較グラフ保存完了: {save_path}")

    return save_path
