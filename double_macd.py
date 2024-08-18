from MyTT import *


def tdx_raw2_kline(r_path, period):
    df = pd.read_csv(r_path, sep="\t", skiprows=1, encoding="gbk")[:-1]
    df.columns = ["date", "time", "open", "high", "low", "close", "vol", "turnover"]
    df["time"] = df["time"].astype(int).astype(str).str.zfill(4)
    df["date"] = df["date"].str.replace("/", "-")
    df["vol"] = df["vol"].astype(int)
    df["tdx_dt"] = (
        df["date"].str[:]
        + " "
        + df["time"].str[0:2]
        + ":"
        + df["time"].str[2:4]
        + ":00"
    )
    df["tdx_dt"] = pd.to_datetime(df["tdx_dt"])

    def add_day_if_before_11(time):
        if time.hour <= 11:
            return time + pd.Timedelta(days=1)
        return time

    df["dt"] = df["tdx_dt"].apply(add_day_if_before_11)
    df["dt"] = pd.to_datetime(df["dt"])

    df["dt_us"] = (
        pd.to_datetime(df["dt"], utc=False)
        .dt.tz_localize("Asia/Shanghai")
        .dt.tz_convert("America/New_York")
    )

    df = df[["dt_us", "open", "close", "high", "low", "vol", "turnover"]]
    df.columns = ["dt", "open", "close", "high", "low", "vol", "turnover"]
    df["dt_1D"] = df.dt.dt.strftime("%Y%m%d")

    ret = df.groupby("dt_1D").agg(
        # dt_1D=("dt_1D", "first"),
        open=("open", "first"),
        close=("close", "last"),
        high=("high", "max"),
        low=("low", "min"),
        vol=("vol", "sum"),
        turnover=("turnover", "sum"),
    )
    ret = ret.reset_index()
    return ret


def huice(data):
    for i in range(len(data)):
        if i <= 2:
            continue
        elif (
            data.loc[i, "m1"] > 0
            and data.loc[i, "m2"] < 0
            and abs(data.loc[i, "m1"]) > abs(data.loc[i, "m2"])*2
            and (
                data.loc[i - 2, "m2"] >= data.loc[i - 1, "m2"]
                and data.loc[i, "m2"] > data.loc[i - 1, "m2"]
            )
        ):
            data.loc[i, "long"] = 1
    return data


if __name__ == "__main__":
    data = tdx_raw2_kline("./data_tdx_raw/74#TQQQ.txt", period="1D")
    m1 = MACD(data.close, 55, 89, 1)
    m2 = MACD(data.close, 13, 21, 1)
    data["m1"] = m1[0]
    data["m2"] = m2[0]
    data["long"] = 0
    data["short"] = 0
    data = huice(data)
    data.to_csv('./data_huice_2/dm_TQQQ.csv')

    print(1)
