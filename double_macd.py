from MyTT import *
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from plotly.subplots import make_subplots



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

    # 判断是否是v形
    def is_v(data, i, col, pre_length, post_length, direction):
        i_seq = list(range(i - pre_length - post_length, i + 1))
        diffs = np.array(
            data.loc[i_seq, col].diff().reset_index(drop=True).drop(index=0)
        )
        if (
            direction == "bottom"
            and (diffs[0:pre_length] < 0).all()
            and (diffs[pre_length : pre_length + post_length] > 0).all()
        ):
            return True

        if (
            direction == "top"
            and (diffs[0:pre_length] > 0).all()
            and (diffs[pre_length : pre_length + post_length] < 0).all()
        ):
            return True
        return False

    def is_chuan(data, i, col, pre_length, post_length, direction, thresh):
        i_seq = list(range(i - pre_length - post_length, i + 1))
        ret = np.array(data.loc[i_seq, col].reset_index(drop=True))
        if (
            direction == "up"
            and (ret[0:pre_length] < thresh).all()
            and (ret[pre_length : pre_length + post_length] > thresh).all()
        ):
            return True
        if (
            direction == "down"
            and (ret[0:pre_length] > thresh).all()
            and (ret[pre_length : pre_length + post_length] < thresh).all()
        ):
            return True
        return False

    for i in range(len(data)):
        if i <= 2:
            continue
        # 做多
        elif (
            data.loc[i, "m1"] > 0
            and abs(data.loc[i, "m1"]) > 1
            # and data.loc[i, "m2"] < 0
            and abs(data.loc[i, "m1"]) > abs(data.loc[i, "m2"]) * 2
            # and is_v(data,i,'m2',2,2,"bottom")
            and is_chuan(data, i, "m2", 1, 1, "up", 0)
        ):
            data.loc[i, "long"] = 1
        # 做空
        elif (
            data.loc[i, "m1"] < 0
            and abs(data.loc[i, "m1"]) > 1
            # and data.loc[i, "m2"] > 0
            and abs(data.loc[i, "m1"]) > abs(data.loc[i, "m2"]) * 2
            # and is_v(data,i,'m2',2,2,"top")
            and is_chuan(data, i, "m2", 1, 1, "down", 0)
        ):
            data.loc[i, "short"] = 1
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
    data.to_csv("./data_huice_dm/TQQQ_dm.csv")

    long_signals = data[data.long > 0].reset_index(drop=True)
    short_signals = data[data.short > 0].reset_index(drop=True)
    kline_1D = go.Candlestick(
        x=data["dt_1D"],
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
    )
    trace_1 = go.Scatter(
        x=long_signals["dt_1D"],
        y=long_signals["close"] * 0.9,
        mode="markers",
        marker=dict(symbol="triangle-up",size=10),
        name="做多",
    )
    trace_2 = go.Scatter(
        x=short_signals["dt_1D"],
        y=short_signals["close"] * 1.2,
        mode="markers",
        marker=dict(symbol="triangle-down",size=10),
        name="做空",
    )
    fig = make_subplots(
        rows=2,
        cols=1,
        # row_heights=[1,0.5,0.5,0.5],
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(""),
        row_width=[1, 1],
    )

    # fig = go.Figure(data=[kline_1D, trace_1, trace_2])
    fig.add_trace(kline_1D,row=1,col=1)
    fig.add_trace(trace_1, row=1, col=1)
    fig.add_trace(trace_2, row=1, col=1)
    fig.add_trace(go.Scatter(x=data['dt_1D'],y=data['m1']),row=2,col=1)
    fig.add_trace(go.Scatter(x=data['dt_1D'], y=data['m2']), row=2, col=1)
    fig.add_trace(go.Scatter(x=long_signals['dt_1D'], y=[0]*len(long_signals),mode="markers"), row=2, col=1)
    fig.add_trace(go.Scatter(x=short_signals['dt_1D'], y=[0]*len(long_signals),mode="markers"), row=2, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False)

    fig.show()
    print(1)
    print(len(long_signals),len(short_signals))
