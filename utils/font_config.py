"""
クロスプラットフォーム対応の日本語フォント設定
"""
import os
import platform
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def setup_japanese_font() -> None:
    """
    クロスプラットフォーム対応の日本語フォント設定

    OS別にフォントパスを検索し、matplotlibの日本語フォントを設定する。
    フォントが見つからない場合はフォールバックフォントを使用する。

    対応OS:
        - macOS: ヒラギノ角ゴシック系
        - Windows: Yu Gothic / MS Gothic / Meiryo
        - Linux: Noto Sans CJK JP
    """
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            _setup_macos_font()
        elif system == "Windows":
            _setup_windows_font()
        else:  # Linux
            _setup_linux_font()
    except Exception as e:
        logger.warning(f"フォント設定中にエラーが発生しました: {e}")
        _setup_fallback_font()

    # マイナス記号の文字化け対策（全OS共通）
    plt.rcParams['axes.unicode_minus'] = False


def _setup_macos_font() -> None:
    """macOS用のフォント設定"""
    font_paths = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/ヒラギノ角ゴ ProN W3.otf"
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_prop = fm.FontProperties(fname=font_path)
                plt.rcParams["font.family"] = font_prop.get_name()
                logger.info(f"✅ 使用フォント (macOS): {font_prop.get_name()}")
                return
            except Exception as e:
                logger.debug(f"フォント読み込み失敗: {font_path} - {e}")
                continue

    # フォールバック
    plt.rcParams['font.family'] = ['Hiragino Sans', 'DejaVu Sans']
    logger.info("✅ 使用フォント (macOS): Hiragino Sans (fallback)")


def _setup_windows_font() -> None:
    """Windows用のフォント設定"""
    try:
        # Windows 10/11の標準日本語フォント
        plt.rcParams['font.family'] = ['Yu Gothic', 'MS Gothic', 'Meiryo', 'DejaVu Sans']
        logger.info("✅ 使用フォント (Windows): Yu Gothic")
    except Exception as e:
        logger.debug(f"Windows フォント設定エラー: {e}")
        plt.rcParams['font.family'] = ['MS Gothic', 'DejaVu Sans']
        logger.info("✅ 使用フォント (Windows): MS Gothic (fallback)")


def _setup_linux_font() -> None:
    """Linux用のフォント設定"""
    plt.rcParams['font.family'] = ['Noto Sans CJK JP', 'DejaVu Sans']
    logger.info("✅ 使用フォント (Linux): Noto Sans CJK JP")


def _setup_fallback_font() -> None:
    """フォールバックフォント設定"""
    plt.rcParams['font.family'] = ['DejaVu Sans']
    logger.warning("⚠️ 日本語フォントが見つかりません。DejaVu Sansを使用します（日本語は表示されない可能性があります）")


def get_current_font_family() -> Optional[str]:
    """
    現在設定されているフォントファミリを取得

    Returns:
        str: フォントファミリ名、取得失敗時はNone
    """
    try:
        return plt.rcParams.get('font.family', [None])[0]
    except Exception:
        return None
