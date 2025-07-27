from flask import Flask, request, render_template, redirect, url_for
from model_utils import process_and_predict
import os

# グローバル変数（予測結果保存用）
rmse = None
r2 = None
plot_path = None
predictions_by_ward = None
actual_prices_by_ward = None
era_predictions = None

# Flask アプリ作成
app = Flask(__name__, template_folder="templates")

# トップページ（CSVアップロード）
@app.route("/", methods=["GET", "POST"])
def upload_file():
    global rmse, r2, plot_path, predictions_by_ward, actual_prices_by_ward, era_predictions
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            os.makedirs("input", exist_ok=True)
            filepath = os.path.join("input", file.filename)
            file.save(filepath)

            # CSVを使って予測を実行
            rmse, r2, plot_path, predictions_by_ward, actual_prices_by_ward, era_predictions = process_and_predict(filepath)

            # 結果概要ページへリダイレクト
            return redirect(url_for("result_overview"))

    return render_template("upload.html")

# 結果概要ページ（RMSEやスコア・リンク）
@app.route("/result_overview")
def result_overview():
    return render_template("result_overview.html", rmse=rmse, r2=r2)


# 区ごとの予測ページ
@app.route("/result_by_ward")
def result_by_ward():
    return render_template(
        "result_by_ward.html",
        predictions=predictions_by_ward,
        actuals=actual_prices_by_ward
    )


# 築年帯ごとの予測ページ
@app.route("/result_by_era")
def result_by_era():
    return render_template(
        "result_by_era.html",
        eras=era_predictions
    )


# グラフの表示ページ（散布図や年次推移）
@app.route("/result_graphs")
def result_graphs():
    return render_template(
        "result_graphs.html",
        image_path=plot_path
    )


if __name__ == "__main__":
    app.run(debug=True, port=5002)
