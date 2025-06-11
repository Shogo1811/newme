import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # これを追加してGUIを使わないようにする
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score


def parse_distance(distance):
    if isinstance(distance, str):
        if "H" in distance:
            parts = distance.replace("分", "").split("H")
            hours = int(parts[0]) * 60
            minutes = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            return hours + minutes
        elif "～" in distance:
            parts = distance.replace("分", "").split("～")
            return (int(parts[0]) + int(parts[1])) / 2
        elif "分" in distance:
            return int(distance.replace("分", ""))
    return distance

def process_and_predict(file_path: str, plot_path: str = "static/result.png"):
    import matplotlib.font_manager as fm
    import os

    font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"  # macOS用パス

    if os.path.exists(font_path):
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams["font.family"] = font_prop.get_name()
        print(f"✅ 使用フォント: {font_prop.get_name()}")
    else:
        print("⚠ 日本語フォントが見つかりません。グラフの文字が表示されない可能性があります。")
    df = pd.read_csv(file_path, encoding="cp932")
    df.columns = df.columns.str.replace("\ufeff", "")

    # 必要なカラム
    columns_to_use = ["取引価格（総額）", "面積（㎡）", "最寄駅：距離（分）", "建築年", "市区町村名", "取引時期"]
    df = df[columns_to_use]

    df["建築年"] = pd.to_numeric(df["建築年"].str.replace("年", ""), errors="coerce")
    df["最寄駅：距離（分）"] = df["最寄駅：距離（分）"].apply(parse_distance)
    df["取引年"] = df["取引時期"].str.extract(r"(\d{4})").astype(float)
    df["築年帯"] = pd.cut(
        2025 - df["建築年"],
        bins=[0, 10, 20, 999],
        labels=["築10年未満", "築10～20年", "築20年以上"]
    )

    df = df.dropna()

    # ダミー変数化
    df = pd.get_dummies(df.drop(columns=["取引時期"]), columns=["市区町村名", "築年帯"], drop_first=True)

    X = df.drop("取引価格（総額）", axis=1)
    y = df["取引価格（総額）"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(random_state=42)
    model.fit(X_train, y_train)
    y_pred = np.round(model.predict(X_test), 2)

    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # 散布図作成
    comparison = pd.DataFrame({"Actual Price": y_test.values, "Predicted Price": y_pred.astype(int)})
    filtered = comparison[(comparison["Actual Price"] < 250000000) & (comparison["Predicted Price"] < 250000000)]

    plt.figure(figsize=(8, 8))
    ax = plt.gca()
    ticks = np.arange(0, 2.1e8, 5e7)
    ax.set_xlim(0, 2e8)
    ax.set_ylim(0, 2e8)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f"{int(val / 1e6):,}"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f"{int(val / 1e6):,}"))
    ax.grid(which="major", linestyle="--", linewidth=0.5)
    plt.scatter(filtered["Actual Price"], filtered["Predicted Price"], color="orange", alpha=0.7)
    plt.plot([0, 2e8], [0, 2e8], '--r', linewidth=2)
    plt.xlabel("Actual Price (x 1,000,000)")
    plt.ylabel("Predicted Price (x 1,000,000)")
    plt.title("Comparison of Actual vs Predicted Prices")
    plt.savefig(plot_path)
    plt.close()

    # 区ごとの予測・実価格
    model_all = RandomForestRegressor(random_state=42)
    model_all.fit(X, y)
    predictions = model_all.predict(X)

    original_df = pd.read_csv(file_path, encoding="cp932")
    original_df.columns = original_df.columns.str.replace("\ufeff", "")
    original_df = original_df.loc[df.index]
    original_df["Predicted Price"] = predictions

    ward_predictions = original_df.groupby("市区町村名")["Predicted Price"].mean().round().astype(int).to_dict()
    ward_actuals = original_df.groupby("市区町村名")["取引価格（総額）"].mean().round().astype(int).to_dict()

    # 築年帯ごとの予測価格
    original_df["建築年"] = pd.to_numeric(original_df["建築年"].str.replace("年", ""), errors="coerce")
    original_df["築年帯"] = pd.cut(
        2025 - original_df["建築年"],
        bins=[0, 10, 20, 999],
        labels=["築10年未満", "築10～20年", "築20年以上"]
    )
    by_ward_and_era = (
        original_df.groupby(["市区町村名", original_df["築年帯"]])["Predicted Price"]
        .mean()
        .unstack()
        .fillna(0)
        .round()
        .astype(int)
        .to_dict(orient="index")
    )

    # 年度別価格推移グラフ
    original_df["取引年"] = original_df["取引時期"].str.extract(r"(\d{4})").astype(float)
    yearly_price = original_df.groupby("取引年")["取引価格（総額）"].mean().dropna().sort_index()

    plt.figure(figsize=(10, 6))
    yearly_price.plot(marker="o")
    plt.title("年度ごとの平均取引価格推移")
    plt.xlabel("取引年")
    plt.ylabel("平均価格")
    plt.grid(True)
    plt.savefig("static/yearly_trend.png")
    plt.close()

    return rmse, r2, plot_path, ward_predictions, ward_actuals, by_ward_and_era
