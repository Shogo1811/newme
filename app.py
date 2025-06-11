from flask import Flask, request, render_template, redirect, url_for
from model_utils import process_and_predict, parse_distance
import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

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


# # TODO 予測ページ動作検証中のため、コメントアウト
# # 個別入力による予測ページ
# @app.route("/predict_input", methods=["GET", "POST"])
# def predict_input():
#     predicted_price = None
#     if request.method == "POST":
#         area = request.form["area"]
#         size = float(request.form["size"])
#         age = int(request.form["age"])
#         distance = int(request.form["distance"])

#         current_year = 2025
#         build_year = current_year - age

#         input_df = pd.DataFrame([{
#             "面積（㎡）": size,
#             "最寄駅：距離（分）": distance,
#             "建築年": build_year,
#             "市区町村名": area
#         }])

#         # データ読み込みと整形
#         df = pd.read_csv("./input/Tokyo_20242_20242.csv", encoding="cp932")
#         df["建築年"] = pd.to_numeric(df["建築年"].str.replace("年", ""), errors="coerce")
#         df["最寄駅：距離（分）"] = df["最寄駅：距離（分）"].apply(parse_distance)

#         df = df.dropna()
#         df = pd.get_dummies(
#             df,
#             columns=["市区町村名", "都道府県名", "種類", "価格情報区分", "間取り", "建物の構造", "用途", "都市計画"],
#             drop_first=True
#         )
#         df = df.drop(columns=["地区名", "最寄駅：名称", "今後の利用目的", "改装", "取引の事情等", "取引時期"])

#         all_columns = df.drop("取引価格（総額）", axis=1).columns
#         input_df = pd.get_dummies(input_df, columns=["市区町村名"])
#         for col in all_columns:
#             if col not in input_df.columns:
#                 input_df[col] = 0
#         input_df = input_df[all_columns]

#         # モデル学習と予測
#         X = df.drop("取引価格（総額）", axis=1)
#         y = df["取引価格（総額）"]
#         model = RandomForestRegressor(random_state=42)
#         model.fit(X, y)
#         predicted_price = model.predict(input_df)[0]

#     return render_template("predict_input.html", predicted_price=predicted_price)


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
