import numpy as np
from MyTT import *
import plotly.graph_objects as go
import pandas as pd
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
    if period == '1D':
        df["dt_period"] = df.dt.dt.strftime("%Y%m%d")
        ret = df.groupby("dt_period").agg(
            # dt_period=("dt_period", "first"),
            open=("open", "first"),
            close=("close", "last"),
            high=("high", "max"),
            low=("low", "min"),
            vol=("vol", "sum"),
            turnover=("turnover", "sum"),
        )
        ret = ret.reset_index()
    if 'min' in period:
        p = int(period.split('min')[0])
        df['time_group_ind'] = df.index // p
        df['dt_period'] = df.dt.dt.strftime("%Y%m%d%H%M%S")
        ret = df.groupby("time_group_ind").agg(
            dt=("dt", "first"),
            dt_period=("dt_period", "first"),
            open=("open", "first"),
            close=("close", "last"),
            high=("high", "max"),
            low=("low", "min"),
            vol=("vol", "sum"),
            turnover=("turnover", "sum"),
        )
        ret = ret.reset_index(drop=True)

    return ret


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
    return (data.loc[i - length + 1: i, col] > 0).all()


def is_neg(data, i, col, length):
    if i < length:
        return 0
    return (data.loc[i - length + 1: i, col] < 0).all()


def double_macd(data, short1=55, long1=89, m1=1, short2=13, long2=21, m2=1):
    m1 = MACD(data.close, short1, long1, m1)[0]
    m2 = MACD(data.close, short2, long2, m2)[0]
    data["m1"] = m1
    data["m2"] = m2
    macd_sell_sig = (m2 > 0) & (m1 < 0) & (m2 < REF(m2, 1))
    macd_buy_sig = (m2 < 0) & (m1 > 0) & (m2 > REF(m2, 1))
    data['macd_buy_signal'] = macd_buy_sig
    data['macd_sell_signal'] = macd_sell_sig
    return data


def jw(data):
    # STICKLINE(JW >= 80 AND JW < MAJW AND REF(JW, 1) > REF(MAJW, 1), JW + 20, 80, 5, 0) ,COLOR00FF00;
    # STICKLINE(JW < 20 AND JW > MAJW AND REF(JW, 1) < REF(MAJW, 1), JW - 20, 20, 5, 0), COLORFF00FF;
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
    MAJW = SMA(JW, 5, 1)
    jw_sell_signal = (JW >= 80) & (JW < MAJW) & (REF(JW, 1) > REF(MAJW, 1))
    jw_buy_signal = (JW < 20) & (JW > MAJW) & (REF(JW, 1) < REF(MAJW, 1))
    data["jw"] = JW
    data['jw_buy_signal'] = jw_buy_signal
    data['jw_sell_signal'] = jw_sell_signal
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
        duanxian_bug_sig = data["duanxian"] > 0
        duanxian_sell_sig = data["duanxian"] <= 0
        data["duanxian_buy_signal"] = duanxian_bug_sig
        data["duanxian_sell_signal"] = duanxian_sell_sig
        return data
    except:
        print("短线操盘error")


def draw_line_jw_duanxian(data):
    fig = make_subplots(
        rows=4,
        cols=1,
        # row_heights=[1,0.5,0.5,0.5],
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(""),
        row_width=[1, 1, 1, 2],
    )

    kline_1D = go.Candlestick(
        x=data["dt_period"],
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
    )

    jw_buy_sig = data[data.jw_buy_signal > 0].reset_index(drop=True)
    jw_sell_sig = data[data.jw_sell_signal > 0].reset_index(drop=True)
    macd_buy_signal = data[data.macd_buy_signal > 0].reset_index(drop=True)
    macd_sell_signal = data[data.macd_sell_signal > 0].reset_index(drop=True)
    huice_long_buy = data[data.huice_long_buy > 0].reset_index(drop=True)
    huice_long_sell = data[data.huice_long_sell > 0].reset_index(drop=True)
    fig.add_trace(kline_1D, row=1, col=1)
    fig.add_trace(
        go.Scatter(
            x=huice_long_buy["dt_period"], y=huice_long_buy['open'] * 0.95, mode="markers",
            marker=dict(symbol='triangle-up', color='red', size=10)
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=huice_long_sell["dt_period"], y=huice_long_sell['open'] * 1.05, mode="markers+text",
            marker=dict(symbol='triangle-down', color='green', size=10), text=[
                "{:.1f}%".format(p * 100)
                for p in np.array(huice_long_sell["profit_rate"])
            ],
            textposition="bottom center",
            textfont=dict(size=16, color="black")
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=macd_buy_signal["dt_period"], y=[0] * len(macd_buy_signal), mode="markers",
            marker=dict(symbol='diamond', color='red', size=5)
        ),
        row=2,
        col=1,
    )

    fig.add_trace(go.Scatter(x=data["dt_period"], y=data["m1"], marker=dict(color='black')), row=2, col=1)
    fig.add_trace(go.Scatter(x=data["dt_period"], y=data["m2"], marker=dict(color='blue')), row=2, col=1)

    fig.add_trace(
        go.Scatter(
            x=macd_buy_signal["dt_period"], y=[0] * len(macd_buy_signal), mode="markers",
            marker=dict(symbol='diamond', color='red', size=5)
        ),
        row=2,
        col=1,
    )
    # fig.add_trace(go.Scatter(x=data["dt_period"], y=data['R6'],marker=dict(color=np.where(data['duanxian'] > 0, 'red', 'green'))), row=3, col=1)
    fig.add_trace(go.Scatter(x=data[data.duanxian >= 0]["dt_period"], y=data[data.duanxian >= 0]['R6'], mode="markers",
                             marker=dict(symbol='square', color='red', size=3)), row=3, col=1)
    fig.add_trace(go.Scatter(x=data[data.duanxian < 0]["dt_period"], y=data[data.duanxian < 0]['R6'], mode="markers",
                             marker=dict(symbol='square', color='green', size=3)), row=3, col=1)

    fig.add_trace(go.Scatter(x=data["dt_period"], y=data['jw']), row=4, col=1)
    fig.add_trace(
        go.Scatter(
            x=jw_buy_sig["dt_period"], y=jw_buy_sig['jw'], mode="markers",
            marker=dict(symbol='diamond', color='red', size=5)
        ),
        row=4,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=jw_sell_sig["dt_period"], y=jw_sell_sig['jw'], mode="markers",
            marker=dict(symbol='diamond', color='green', size=5)
        ),
        row=4,
        col=1,
    )

    fig.update_layout(xaxis_rangeslider_visible=False)
    # fig.show()
    fig.write_image("./data_huice_dm/" + "macd_jw_duan_debug_fig.jpg", width=1920, height=1080)
    # macd_in_signals = data[data.long_in > 0].reset_index(drop=True)


def merge_macd_duanxian(data):
    # 采用macd和短线同时出现信号的时候进行开仓
    data['macd_duanxian'] = data['macd_buy_signal'].astype(int) + data['duanxian_buy_signal'].astype(int)
    data['macd_duanxian_buy_signal'] = (data['macd_buy_signal'].astype(int) + data['duanxian_buy_signal'].astype(
        int)) >= 2
    return data


def huice(data, in_sig_col='macd_duanxian_buy_signal', out_sig_col='duanxian_sell_signal'):
    # 找到连续买信号的起点作为买点
    in_indexs = data[data[in_sig_col] > 0].index
    in_indexs_starts = []
    for index in in_indexs:
        if index - 1 not in in_indexs:
            in_indexs_starts.append(index)
    # 找离买点最近的卖点
    in_indexs_starts.reverse()
    out_indexs = []
    profit_rates = []
    for index in in_indexs_starts:
        for j in range(index, len(data)):
            if data.loc[j, out_sig_col] > 0:
                out_indexs.append(j)
                profit_rates.append(data.loc[j + 1, 'open'] / data.loc[index + 1, 'open'] - 1)
                break
            if j == len(data) - 1:
                out_indexs.append(-1)
                profit_rates.append(0)
    data.loc[np.array(in_indexs_starts) + 1, 'huice_long_buy'] = 1
    data.loc[np.array(out_indexs) + 1, 'huice_long_sell'] = 1
    data.loc[np.array(out_indexs) + 1, 'profit_rate'] = np.array(profit_rates)
    return data


if __name__ == "__main__":
    codes = ['TQQQ']
    # codes = ['TQQQ','TSLA','MSFT','AAPL','AMD','BABA','GOOGL','NVDA','PDD']
    for code in codes:
        # 390min是一天，多天的就按分钟计算好了
        data = tdx_raw2_kline("./data_tdx_raw/74#" + code + ".txt", period="390min")
        data = double_macd(data, 36, 78, 1, 12, 26, 1)
        data = jw(data)
        data = duanxian(data)
        data = merge_macd_duanxian(data)
        data = huice(data,'duanxian_buy_signal','duanxian_sell_signal')
        draw_line_jw_duanxian(data)
        print(1)
        print(data.profit_rate.sum())
