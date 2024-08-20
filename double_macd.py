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


def longport_kline(agent, period):
    resp = agent.get_data_1D("TQQQ")
    print(1)


def calc_buy_sell_point(data):
    # 判断是否是v形
    def is_v(data, i, col, pre_length, post_length, direction):
        if i<pre_length+post_length:
            return False
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

    # 判断是否穿0轴
    def is_chuan(data, i, col, pre_length, post_length, direction, thresh):
        if i < pre_length+post_length:
            return False
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

    def speed(data,i,col,length):
        if i<length:
            return 0
        return abs((data.loc[i-length,col]-data.loc[i,col])/length)

    data["long"] = 0
    data["short"] = 0
    data["long_stop"] = 0
    data["short_stop"] = 0
    for i in range(len(data)):
        # 做多开单条件，多个append的条件是或的关系，下同
        long_rules = []
        long_rules.append(
            data.loc[i, "m1"] > 0
            and abs(data.loc[i, "m1"]) > 1
            and is_chuan(data, i, "m2", 1, 1, "up", 0)
            and speed(data,i,"m2",2)>0.1
        )
        long_rules.append(
            data.loc[i, "m1"] > 0
            and abs(data.loc[i, "m1"]) > 1
            and data.loc[i, "m2"] < 0
            and is_v(data, i, "m2", 3, 3, "bottom")
            and abs(data.loc[i, "m1"]) >= 2 * abs(data.loc[i, "m2"])
        )
        # 做多止盈止损条件
        long_stop_rules = []
        long_stop_rules.append(is_chuan(data,i,"m2",1,1,"down",0))
        long_stop_rules.append(is_v(data, i, "m2", 3, 3, "top"))
        long_stop_rules.append(speed(data,i,"m2",2)<0.01)

        # 做空开单条件
        short_rules = []
        short_rules.append(
            data.loc[i, "m1"] < 0
            and abs(data.loc[i, "m1"]) > 1
            and is_chuan(data, i, "m2", 1, 1, "down", 0)
            and speed(data, i, "m2", 2) > 0.1
        )
        short_rules.append(
            data.loc[i, "m1"] < 0
            and abs(data.loc[i, "m1"]) > 1
            and data.loc[i, "m2"] > 0
            and is_v(data, i, "m2", 3, 3, "top")
            and abs(data.loc[i, "m1"]) >= 2 * abs(data.loc[i, "m2"])
        )
        # 做空止盈止损条件
        short_stop_rules = []
        short_stop_rules.append(is_chuan(data,i,"m2",1,1,"up",0))
        short_stop_rules.append(is_v(data, i, "m2", 3, 3, "bottom"))
        short_stop_rules.append(speed(data,i,"m2",2)<0.01)

        if i <= 2:
            continue
        # 做多
        if sum(long_rules) > 0:
            data.loc[i, "long"] = 1
        # 做空
        if sum(short_rules) > 0:
            data.loc[i, "short"] = 1
        # 多单了结
        if sum(long_stop_rules) > 0:
            data.loc[i, "long_stop"] = 1
        # 空单了结
        if sum(short_stop_rules) > 0:
            data.loc[i, "short_stop"] = 1

    return data


def double_macd(data):
    m1 = MACD(data.close, 55, 89, 1)
    m2 = MACD(data.close, 13, 21, 1)
    data["m1"] = m1[0]
    data["m2"] = m2[0]
    return data

def huice(data):
    data['long_in'],data['long_out'],data['short_in'],data['short_out']=0,0,0,0
    # data['profit_rate'] = 0

    long_in_ids = data[data['long']==1].index
    short_in_ids = data[data['short']==1].index
    for id in long_in_ids:
        find_area = data.iloc[id+1:]
        first_long_end = find_area[find_area["long_stop"]==1].index[0]
        data.loc[id,'long_in']=1
        data.loc[first_long_end,"long_out"]=1
        data.loc[first_long_end,'profit_rate'] = data.loc[first_long_end+1,'open']/data.loc[id+1,'open']-1
    for id in short_in_ids:
        find_area = data.iloc[id + 1:]
        first_short_end = find_area[find_area["short_stop"] == 1].index[0]
        data.loc[id, 'short_in'] = 1
        data.loc[first_short_end, "short_out"] = 1
        data.loc[first_short_end,'profit_rate'] = (data.loc[id+1,'open'] - data.loc[first_short_end+1,'open'])/data.loc[id+1,'open']

    return data


def draw_line(data, code=""):
    long_in_signals = data[data.long_in > 0].reset_index(drop=True)
    short_in_signals = data[data.short_in > 0].reset_index(drop=True)
    long_out_signals = data[data.long_out > 0].reset_index(drop=True)
    short_out_signals = data[data.short_out > 0].reset_index(drop=True)
    # long_profit_rates = data[data.long_out>0].reset_index(drop=True)

    kline_1D = go.Candlestick(
        x=data["dt_1D"],
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
    )
    trace_long = go.Scatter(
        x=long_in_signals["dt_1D"],
        y=long_in_signals["close"] * 0.9,
        mode="markers",
        marker=dict(symbol="triangle-up", size=10),
        name="做多",
    )
    trace_short = go.Scatter(
        x=short_in_signals["dt_1D"],
        y=short_in_signals["close"] * 1.2,
        mode="markers",
        marker=dict(symbol="triangle-down", size=10),
        name="做空",
    )

    trace_long_stop = go.Scatter(
        x=long_out_signals["dt_1D"],
        y=long_out_signals["close"] * 0.9,
        # text=long_out_signals['profit_rate'],
        text = ['{:.1f}%'.format(p*100) for p in np.array(long_out_signals['profit_rate'])],
        textposition="bottom center",
        textfont=dict(size=16, color="black"),
        mode="markers+text",
        marker=dict(symbol="arrow-down", size=10),
        name="多单结束",
    )
    trace_short_stop = go.Scatter(
        x=short_out_signals["dt_1D"],
        y=short_out_signals["close"] * 1.2,
        # text = short_out_signals['profit_rate'],
        text=['{:.1f}%'.format(p * 100) for p in np.array(short_out_signals['profit_rate'])],
        textposition="bottom center",
        textfont=dict(size=16, color="black"),
        mode="markers+text",
        marker=dict(symbol="arrow-up", size=10),
        name="空单结束",
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

    # fig = go.Figure(data=[kline_1D, trace_long, trace_short])
    fig.add_trace(kline_1D, row=1, col=1)
    fig.add_trace(trace_long, row=1, col=1)
    fig.add_trace(trace_short, row=1, col=1)
    fig.add_trace(trace_long_stop,row=1,col=1)
    fig.add_trace(trace_short_stop,row=1,col=1)
    fig.add_trace(go.Scatter(x=data["dt_1D"], y=data["m1"]), row=2, col=1)
    fig.add_trace(go.Scatter(x=data["dt_1D"], y=data["m2"]), row=2, col=1)
    fig.add_trace(
        go.Scatter(x=long_in_signals["dt_1D"], y=[0] * len(long_in_signals), mode="markers"),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=short_in_signals["dt_1D"], y=[0] * len(short_in_signals), mode="markers"
        ),
        row=2,
        col=1,
    )

    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_layout(title_text=code)
    print(len(long_in_signals), len(short_in_signals))

    fig.show()


if __name__ == "__main__":
    code = "AMD"
    data = tdx_raw2_kline("./data_tdx_raw/74#" + code + ".txt", period="1D")
    data = double_macd(data)
    data = calc_buy_sell_point(data)
    data = huice(data)
    data.to_csv("./data_huice_dm/" + code + ".csv")
    draw_line(data, code)
    print(data['profit_rate'].sum())
