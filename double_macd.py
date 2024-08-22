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


def speed_abs(data, i, col, length):
    if i < length:
        return 0
    return abs((data.loc[i, col] - data.loc[i - length, col]) / length)


def speed(data, i, col, length):
    if i < length:
        return 0
    return (data.loc[i, col] - data.loc[i - length, col]) / length


def is_pos(data, i, col, length):
    if i < length:
        return 0
    return (data.loc[i - length + 1 : i, col] > 0).all()


def is_neg(data, i, col, length):
    if i < length:
        return 0
    return (data.loc[i - length + 1 : i, col] < 0).all()


def calc_buy_sell_point(data):
    # 判断是否是v形
    def is_v(data, i, col, pre_length, post_length, direction):
        if i < pre_length + post_length:
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
        if i < pre_length + post_length:
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
            and speed_abs(data, i, "m2", 2) > 0.1
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
        long_stop_rules.append(is_chuan(data, i, "m2", 1, 1, "down", 0))
        long_stop_rules.append(is_v(data, i, "m2", 3, 3, "top"))
        long_stop_rules.append(speed_abs(data, i, "m2", 2) < 0.01)

        # 做空开单条件
        short_rules = []
        short_rules.append(
            data.loc[i, "m1"] < 0
            and abs(data.loc[i, "m1"]) > 1
            and is_chuan(data, i, "m2", 1, 1, "down", 0)
            and speed_abs(data, i, "m2", 2) > 0.1
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
        short_stop_rules.append(is_chuan(data, i, "m2", 1, 1, "up", 0))
        short_stop_rules.append(is_v(data, i, "m2", 3, 3, "bottom"))
        short_stop_rules.append(speed_abs(data, i, "m2", 2) < 0.01)

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


def calc_point_duanxian_jw(data):
    data["long_start"], data["long_end"], data["short_start"], data["short_end"] = (
        0,
        0,
        0,
        0,
    )
    for i in range(len(data)):
        long_start_rules, long_end_rules, short_start_rules, short_end_rules = (
            [],
            [],
            [],
            [],
        )
        # 买卖点规则
        long_start_rules.append(
            # is_pos(data, i, "duanxian", 1) and speed(data, i, "jw", 3) > 0 and data.loc[i,'duanxian']>1
            # is_pos(data, i, "duanxian", 3) and is_pos(data, i, "m1", 1) and  data.loc[i,'duanxian']>1
            data.loc[i, "duanxian"]
            > 0
        )
        long_end_rules.append(is_neg(data, i, "duanxian", 2))
        short_start_rules.append(
            # is_neg(data, i, "duanxian", 1) and speed(data, i, "jw", 3) < 0 and data.loc[i,'duanxian']<-1
            # is_neg(data, i, "duanxian", 3) and is_neg(data, i, "m1", 1)  and data.loc[i,'duanxian']<-1
            data.loc[i, "duanxian"]
            < 0
        )
        short_end_rules.append(is_pos(data, i, "duanxian", 2))
        if i < 2:
            continue
        if sum(long_start_rules) > 0:
            data.loc[i, "long_start"] = 1
        if sum(long_end_rules) > 0:
            data.loc[i, "long_end"] = 1
        if sum(short_start_rules) > 0:
            data.loc[i, "short_start"] = 1
        if sum(short_end_rules) > 0:
            data.loc[i, "short_end"] = 1

    # 找连续的多
    long_start_points_ori = np.where(np.diff(data["long_start"]) == 1)[0] + 1
    long_end_points_ori = np.where(np.diff(data["long_start"]) == -1)[0]
    long_end_points_ori = long_end_points_ori[
        long_end_points_ori >= long_start_points_ori[0]
    ]
    long_start_points_ori = long_start_points_ori[
        long_start_points_ori <= long_end_points_ori[-1]
    ]

    # 过滤起点的R6高或者低的点
    long_mask = np.array(data.loc[long_start_points_ori, "R6"] < 50)
    long_start_points = np.array(
        [
            long_start_points_ori[i]
            for i in range(len(long_mask))
            if long_mask[i] == True
        ]
    )
    long_end_points = np.array(
        [long_end_points_ori[i] for i in range(len(long_mask)) if long_mask[i] == True]
    )
    long_start_points += 1
    long_end_points += 2
    long_profits = (
        np.array(data.loc[long_end_points, "open"])
        / np.array(data.loc[long_start_points, "open"])
        - 1
    )

    # 找连续的空
    short_start_points = np.where(np.diff(data["short_start"]) == 1)[0] + 1
    short_end_points = np.where(np.diff(data["short_start"]) == -1)[0]
    short_end_points = short_end_points[short_end_points >= short_start_points[0]]
    short_start_points = short_start_points[short_start_points <= short_end_points[-1]]
    short_start_points += 1
    short_end_points += 2
    short_profits = 1 - np.array(data.loc[short_end_points, "open"]) / np.array(
        data.loc[short_start_points, "open"]
    )

    (
        data.loc[long_start_points, "long_in"],
        data.loc[long_end_points, "long_out"],
        data.loc[short_start_points, "short_in"],
        data.loc[short_end_points, "short_out"],
    ) = (1, 1, 1, 1)
    (
        data.loc[long_end_points, "profit_rate"],
        data.loc[short_end_points, "profit_rate"],
    ) = (long_profits, short_profits)

    print(long_profits.sum() + short_profits.sum())
    return data


def calc_point_duanxian_2(data):
    data["duan_pos"], data["duan_neg"] = 0, 0
    data.loc[data["duanxian"] > 0, "duan_pos"] = 1
    data.loc[data["duanxian"] < 0, "duan_neg"] = 1

    # 就近修改，如果周围前两格之内有0，则改为0
    duan_pos = data['duan_pos']
    duan_neg = data['duan_neg']
    has_0_nearby =np.logical_or(np.array(duan_pos.shift(1))==0, np.array(duan_pos.shift(2))==0,np.array(duan_pos.shift(2))==0)
    data.loc[has_0_nearby,'duan_pos'] = 0
    has_0_nearby =np.logical_or(np.array(duan_neg.shift(1))==0, np.array(duan_neg.shift(2))==0,np.array(duan_neg.shift(2))==0)
    data.loc[has_0_nearby,'duan_neg'] = 0

    long_start_points = np.where(np.diff(data["duan_pos"]) == 1)[0] + 1
    long_end_points = np.where(np.diff(data["duan_pos"]) == -1)[0] + 1
    short_start_points = np.where(np.diff(data["duan_neg"]) == 1)[0] + 1
    short_end_points = np.where(np.diff(data["duan_neg"]) == -1)[0] + 1

    # 提出start和end对不齐的点
    long_end_points = long_end_points[long_end_points >= long_start_points[0]]
    long_start_points = long_start_points[long_start_points <= long_end_points[-1]]
    short_end_points = short_end_points[short_end_points >= short_start_points[0]]
    short_start_points = short_start_points[short_start_points <= short_end_points[-1]]

    # 过滤起点R6
    long_mask = np.array(data.loc[long_start_points, "R6"] < 50)
    long_start_points = np.array(
        [long_start_points[i] for i in range(len(long_mask)) if long_mask[i] == True]
    )
    long_end_points = np.array(
        [long_end_points[i] for i in range(len(long_mask)) if long_mask[i] == True]
    )

    short_mask = np.array(data.loc[short_start_points, "R6"] > 50)
    short_start_points = np.array(
        [short_start_points[i] for i in range(len(short_mask)) if short_mask[i] == True]
    )
    short_end_points = np.array(
        [short_end_points[i] for i in range(len(short_mask)) if short_mask[i] == True]
    )

    long_start_points += 1
    long_end_points += 1
    short_start_points += 1
    short_end_points += 1

    (
        data.loc[long_start_points, "long_start_points"],
        data.loc[long_end_points, "long_end_points"],
        data.loc[short_start_points, "short_start_points"],
        data.loc[short_end_points, "short_end_points"],
    ) = (1, 1, 1, 1)

    long_profits = (
        np.array(data.loc[long_end_points, "open"])
        / np.array(data.loc[long_start_points, "open"])
        - 1
    )
    short_profits = 1 - np.array(data.loc[short_end_points, "open"]) / np.array(
        data.loc[short_start_points, "open"]
    )
    (
        data.loc[long_end_points, "profit_rate"],
        data.loc[short_end_points, "profit_rate"],
    ) = (long_profits, short_profits)
    print(long_profits.sum() + short_profits.sum())

    return data


def double_macd(data):
    m1 = MACD(data.close, 55, 89, 1)
    m2 = MACD(data.close, 13, 21, 1)
    data["m1"] = m1[0]
    data["m2"] = m2[0]
    return data


def jw(data):
    N1 = 45
    M1 = 15
    M2 = 15
    CLOSE = np.array(data["close"])
    HIGH = np.array(data["high"])
    LOW = np.array(data["low"])
    RSV = (CLOSE - LLV(LOW, N1)) / (HHV(HIGH, N1) - LLV(LOW, N1)) * 100
    K = SMA(RSV, M1, 1)
    D = SMA(K, M2, 1)
    JW = 3 * K - 2 * D
    data["jw"] = JW
    return data


def duanxian(data):
    try:
        C = np.array(data["close"])
        L = np.array(data["low"])
        H = np.array(data["high"])
        N = 35
        M = 35
        B1 = (HHV(H, N) - C) / (HHV(H, N) - LLV(L, N)) * 100 - M
        B2 = SMA(B1, N, 1) + 100
        B3 = (C - LLV(L, N)) / (HHV(H, N) - LLV(L, N)) * 100
        B4 = SMA(B3, 3, 1)
        B5 = SMA(B4, 3, 1) + 100
        R6 = B5 - B2
        data["R6"] = R6
        data["duanxian"] = data["R6"].diff()
        return data
    except:
        print("短线操盘error")


def huice(data):
    data["long_in"], data["long_out"], data["short_in"], data["short_out"] = 0, 0, 0, 0
    # data['profit_rate'] = 0

    long_in_ids = data[data["long"] == 1].index
    short_in_ids = data[data["short"] == 1].index
    for id in long_in_ids:
        find_area = data.iloc[id + 1 :]
        first_long_end = find_area[find_area["long_stop"] == 1].index[0]
        data.loc[id, "long_in"] = 1
        data.loc[first_long_end, "long_out"] = 1
        data.loc[first_long_end, "profit_rate"] = (
            data.loc[first_long_end + 1, "open"] / data.loc[id + 1, "open"] - 1
        )
    for id in short_in_ids:
        find_area = data.iloc[id + 1 :]
        first_short_end = find_area[find_area["short_stop"] == 1].index[0]
        data.loc[id, "short_in"] = 1
        data.loc[first_short_end, "short_out"] = 1
        data.loc[first_short_end, "profit_rate"] = (
            data.loc[id + 1, "open"] - data.loc[first_short_end + 1, "open"]
        ) / data.loc[id + 1, "open"]

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
        text=[
            "{:.1f}%".format(p * 100) for p in np.array(long_out_signals["profit_rate"])
        ],
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
        text=[
            "{:.1f}%".format(p * 100)
            for p in np.array(short_out_signals["profit_rate"])
        ],
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
    fig.add_trace(trace_long_stop, row=1, col=1)
    fig.add_trace(trace_short_stop, row=1, col=1)
    fig.add_trace(go.Scatter(x=data["dt_1D"], y=data["m1"]), row=2, col=1)
    fig.add_trace(go.Scatter(x=data["dt_1D"], y=data["m2"]), row=2, col=1)
    fig.add_trace(
        go.Scatter(
            x=long_in_signals["dt_1D"], y=[0] * len(long_in_signals), mode="markers"
        ),
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
    # fig.write_image("./data_huice_dm/"+code+"_fig.png")
    fig.show()


def draw_line_jw_duanxian(data):
    kline_1D = go.Candlestick(
        x=data["dt_1D"],
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
    )


if __name__ == "__main__":
    code = "TQQQ"
    data = tdx_raw2_kline("./data_tdx_raw/74#" + code + ".txt", period="1D")
    data = double_macd(data)
    data = jw(data)
    data = duanxian(data)
    # 双macd
    # data = calc_buy_sell_point(data)
    # data = huice(data)
    # 短线36+jw
    data = calc_point_duanxian_2(data)
    data.to_csv("./data_huice_dm/" + code + ".csv")
    # draw_line(data, code)
    # print(data["profit_rate"].sum())
