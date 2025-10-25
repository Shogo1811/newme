"""
東京23区マンション価格予測 Webアプリケーション（リファクタリング版）
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, render_template, redirect, url_for, flash, session

from config import config
from utils.file_handler import validate_uploaded_file, save_uploaded_file, cleanup_old_files
from services.prediction_service import process_and_predict

# Flask アプリ作成
app = Flask(
    __name__,
    template_folder=config.TEMPLATE_FOLDER,
    static_folder=config.STATIC_FOLDER
)
app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE


def setup_logging():
    """ロギング設定"""
    if not app.debug:
        # ログディレクトリ作成
        os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

        # ファイルハンドラ
        file_handler = RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        file_handler.setLevel(logging.INFO)

        # ルートロガーに追加
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, logging.StreamHandler()]
        )

        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('アプリケーション起動')
    else:
        # デバッグモードでは標準出力のみ
        logging.basicConfig(
            level=logging.DEBUG,
            format=config.LOG_FORMAT
        )


setup_logging()
logger = logging.getLogger(__name__)


# トップページ（CSVアップロード）
@app.route("/", methods=["GET", "POST"])
def upload_file():
    """
    CSVファイルアップロードとモデル予測

    GET: アップロードフォームを表示
    POST: ファイルを保存し、予測処理を実行
    """
    if request.method == "POST":
        file = request.files.get("file")

        # ファイルのバリデーション
        is_valid, error_message = validate_uploaded_file(file)
        if not is_valid:
            flash(error_message, "error")
            logger.warning(f"ファイルバリデーション失敗: {error_message}")
            return redirect(url_for("upload_file"))

        # ファイル保存
        success, filepath, error_message = save_uploaded_file(file)
        if not success:
            flash(error_message, "error")
            logger.error(f"ファイル保存失敗: {error_message}")
            return redirect(url_for("upload_file"))

        logger.info(f"ファイルアップロード成功: {filepath}")

        # 古いファイルのクリーンアップ
        cleanup_old_files(config.UPLOAD_FOLDER, max_files=10)

        # 予測処理実行
        try:
            result = process_and_predict(filepath)

            # セッションに結果を保存
            session['rmse'] = result.rmse
            session['r2'] = result.r2
            session['scatter_plot_path'] = result.scatter_plot_path
            session['trend_plot_path'] = result.trend_plot_path
            session['predictions_by_ward'] = result.predictions_by_ward
            session['actual_prices_by_ward'] = result.actual_prices_by_ward
            session['era_predictions'] = result.era_predictions

            logger.info("予測処理成功")
            flash("予測が完了しました", "success")
            return redirect(url_for("result_overview"))

        except KeyError as e:
            error_msg = f"CSVファイルの形式が不正です。必要なカラムが不足しています: {e}"
            flash(error_msg, "error")
            logger.error(error_msg, exc_info=True)
            return redirect(url_for("upload_file"))

        except ValueError as e:
            error_msg = f"データの処理中にエラーが発生しました: {e}"
            flash(error_msg, "error")
            logger.error(error_msg, exc_info=True)
            return redirect(url_for("upload_file"))

        except Exception as e:
            error_msg = f"予期しないエラーが発生しました: {e}"
            flash(error_msg, "error")
            logger.error(error_msg, exc_info=True)
            return redirect(url_for("upload_file"))

    return render_template("upload.html")


# 結果概要ページ
@app.route("/result_overview")
def result_overview():
    """予測結果の概要を表示"""
    rmse = session.get('rmse')
    r2 = session.get('r2')

    if rmse is None or r2 is None:
        flash("予測結果がありません。CSVファイルをアップロードしてください。", "warning")
        return redirect(url_for("upload_file"))

    return render_template("result_overview.html", rmse=rmse, r2=r2)


# 区ごとの予測ページ
@app.route("/result_by_ward")
def result_by_ward():
    """区ごとの予測価格と実際価格を表示"""
    predictions = session.get('predictions_by_ward')
    actuals = session.get('actual_prices_by_ward')

    if predictions is None or actuals is None:
        flash("予測結果がありません。CSVファイルをアップロードしてください。", "warning")
        return redirect(url_for("upload_file"))

    return render_template(
        "result_by_ward.html",
        predictions=predictions,
        actuals=actuals
    )


# 築年帯ごとの予測ページ
@app.route("/result_by_era")
def result_by_era():
    """築年帯ごとの予測価格を表示"""
    eras = session.get('era_predictions')

    if eras is None:
        flash("予測結果がありません。CSVファイルをアップロードしてください。", "warning")
        return redirect(url_for("upload_file"))

    return render_template("result_by_era.html", eras=eras)


# グラフの表示ページ
@app.route("/result_graphs")
def result_graphs():
    """散布図と年次推移グラフを表示"""
    scatter_path = session.get('scatter_plot_path')
    trend_path = session.get('trend_plot_path')

    if scatter_path is None or trend_path is None:
        flash("予測結果がありません。CSVファイルをアップロードしてください。", "warning")
        return redirect(url_for("upload_file"))

    return render_template(
        "result_graphs.html",
        image_path=scatter_path
    )


# エラーハンドラ
@app.errorhandler(413)
def request_entity_too_large(error):
    """ファイルサイズ超過エラー"""
    max_size_mb = config.MAX_FILE_SIZE / (1024 * 1024)
    flash(f"ファイルサイズが大きすぎます。{max_size_mb}MB以下にしてください。", "error")
    return redirect(url_for("upload_file"))


@app.errorhandler(500)
def internal_server_error(error):
    """内部サーバーエラー"""
    logger.error(f"500エラー: {error}", exc_info=True)
    flash("サーバー内部でエラーが発生しました。", "error")
    return redirect(url_for("upload_file"))


if __name__ == "__main__":
    # 必要なディレクトリを作成
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config.STATIC_FOLDER, exist_ok=True)

    # アプリケーション起動
    app.run(debug=config.DEBUG, port=config.PORT)
