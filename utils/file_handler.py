"""
ファイルアップロード処理とバリデーション
"""
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import Tuple, Optional
import logging

from config import config

logger = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:
    """
    ファイル拡張子が許可されているかチェック

    Args:
        filename (str): チェックするファイル名

    Returns:
        bool: 許可されている場合True
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def validate_uploaded_file(file: Optional[FileStorage]) -> Tuple[bool, str]:
    """
    アップロードされたファイルのバリデーション

    Args:
        file (FileStorage | None): アップロードされたファイル

    Returns:
        Tuple[bool, str]: (バリデーション成功フラグ, エラーメッセージ)
    """
    # ファイル存在チェック
    if not file:
        return False, "ファイルが選択されていません"

    # ファイル名チェック
    if file.filename == "":
        return False, "ファイル名が空です"

    # 拡張子チェック
    if not allowed_file(file.filename):
        allowed_exts = ', '.join(config.ALLOWED_EXTENSIONS)
        return False, f"許可されていないファイル形式です。許可されている形式: {allowed_exts}"

    return True, ""


def save_uploaded_file(file: FileStorage, upload_folder: str = None) -> Tuple[bool, str, str]:
    """
    アップロードされたファイルを安全に保存

    Args:
        file (FileStorage): アップロードされたファイル
        upload_folder (str, optional): 保存先フォルダ。Noneの場合はconfig.UPLOAD_FOLDERを使用

    Returns:
        Tuple[bool, str, str]: (保存成功フラグ, ファイルパス, エラーメッセージ)
    """
    if upload_folder is None:
        upload_folder = config.UPLOAD_FOLDER

    try:
        # アップロードフォルダ作成
        os.makedirs(upload_folder, exist_ok=True)

        # ファイル名のサニタイズ（パストラバーサル対策）
        filename = secure_filename(file.filename)

        # ファイルパス生成
        filepath = os.path.join(upload_folder, filename)

        # ファイル保存
        file.save(filepath)

        logger.info(f"ファイル保存成功: {filepath}")
        return True, filepath, ""

    except OSError as e:
        error_msg = f"ファイル保存に失敗しました（ディスク容量不足またはアクセス権限エラー）: {e}"
        logger.error(error_msg)
        return False, "", error_msg

    except Exception as e:
        error_msg = f"ファイル保存中に予期しないエラーが発生しました: {e}"
        logger.error(error_msg, exc_info=True)
        return False, "", error_msg


def cleanup_old_files(folder: str, max_files: int = 10) -> None:
    """
    古いファイルを削除してストレージを管理

    Args:
        folder (str): クリーンアップ対象のフォルダ
        max_files (int): 保持する最大ファイル数
    """
    try:
        if not os.path.exists(folder):
            return

        # ファイル一覧を取得（更新日時順にソート）
        files = []
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                files.append((filepath, os.path.getmtime(filepath)))

        # 更新日時で降順ソート
        files.sort(key=lambda x: x[1], reverse=True)

        # max_files以降のファイルを削除
        for filepath, _ in files[max_files:]:
            try:
                os.remove(filepath)
                logger.info(f"古いファイルを削除: {filepath}")
            except Exception as e:
                logger.warning(f"ファイル削除失敗: {filepath} - {e}")

    except Exception as e:
        logger.error(f"ファイルクリーンアップ中にエラー: {e}", exc_info=True)
