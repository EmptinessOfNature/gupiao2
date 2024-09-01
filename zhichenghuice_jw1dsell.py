import pandas as pd
import os
import numpy as np
import multiprocessing
from MyTT import *

import longport_utils
from longport_utils import get_atr_longport
from datetime import datetime

# 增加最后30分钟jw拐头卖出逻辑

def huice_1d(data, first_cash, n_atr):
    icon_buy = (
        (
            data["icon_1"].fillna(0)
            + data["icon_38"].fillna(0)
            + data["icon_34"].fillna(0)
            + data["icon_13"].fillna(0)
            + data["icon_11"].fillna(0)
        )
        >= 1
    ).astype(int)
    icon_jw5_30_bottom = (
        ((data["jw5"] < 20).astype(int) + (data["jw30"] < 20).astype(int)) >= 2
    ).astype(int)
    icon_sell = (
        (
            data["icon_2"].fillna(0)
            + data["icon_39"].fillna(0)
            + data["icon_35"].fillna(0)
            + data["icon_12"].fillna(0)
            + data["icon_41"].fillna(0)
        )
        >= 1
    ).astype(int)
    icon_jw5_30_top = (
        ((data["jw5"] > 80).astype(int) + (data["jw30"] > 80).astype(int)) >= 2
    ).astype(int)

    data["buy_signal"] = icon_jw5_30_bottom * icon_buy
    data["sell_signal"] = icon_sell

    for i in range(len(data)):
        zhiying_diff = data.loc[i, "atr5"] * n_atr
        if i == 0:
            act_init_1d(data, i, first_cash)
            sell_no_mod_2 = 0
        else:
            act_init_1line(data, i)
        if data.loc[i, "buy_signal"] == 1 and i < 389 - 30:
            now_cash = data.loc[i, "cash"]
            act_buy(data, i, first_cash, now_cash)
        if data.loc[i, "sell_signal"] == 1:
            if sell_no_mod_2 == 0:
                act_sell_1half(data, i)
            else:
                act_sell_2half(data, i)
            sell_no_mod_2 = 1 - sell_no_mod_2
        max_zhiying_prices = [
            float(j) for j in data.loc[i, "max_zhiying_prices"].split(";")[0:-1]
        ]
        if (
            np.array(max_zhiying_prices) - float(data.loc[i, "open"]) >= zhiying_diff
        ).any():
            act_sell_zhiying(data, i, zhiying_diff)
        if i==389-30:
            if data.loc[i,'jw1']<data.loc[i-1,'jw1']:
                act_sell_2half(data,i)
        if i == 389 - 3:
            act_sell_2half(data, i)

    return data, float(data.cash.iloc[-1])


def act_sell_zhiying(data, i, zhiying_diff):
    max_zhiying_prices = [
        float(j) for j in data.loc[i, "max_zhiying_prices"].split(";")[0:-1]
    ]
    all_chicang = data.loc[i, "chicang"].split(";")[0:-1]
    chicang_prices = [float(j.split(":")[0]) for j in all_chicang]
    chicang_nums = [float(j.split(":")[1]) for j in all_chicang]
    sell_nums = [0] * len(all_chicang)
    sell_cash = 0
    profit = 0
    for j in range(len(all_chicang)):
        if max_zhiying_prices[j] - data.loc[i, "open"] >= zhiying_diff:
            sell_nums[j] = chicang_nums[j]
            chicang_nums[j] = 0
            sell_cash += sell_nums[j] * data.loc[i, "open"]
            profit += (data.loc[i, "open"] - chicang_prices[j]) * sell_nums[j]
            data.loc[i, "sell_detail"] += (
                str(data.loc[i, "open"]) + ":" + str(sell_nums[j]) + ";"
            )
    data.loc[i, "cash"] = data.loc[i, "cash"] + sell_cash
    data.loc[i, "profit"] = profit
    data.loc[i, "chicang"] = ""
    data.loc[i, "max_zhiying_prices"] = ""

    for j in range(len(chicang_nums)):
        if chicang_nums[j] != 0:
            data.loc[i, "chicang"] += (
                str(chicang_prices[j]) + ":" + str(chicang_nums[j]) + ";"
            )
            data.loc[i, "max_zhiying_prices"] += str(max_zhiying_prices[j]) + ";"


def act_sell_1half(data, i):
    if data.loc[i, "chicang"] == "":
        return
    all_chicang = data.loc[i, "chicang"].split(";")[0:-1]
    chicang_prices = [float(j.split(":")[0]) for j in all_chicang]
    chicang_nums = [float(j.split(":")[1]) for j in all_chicang]
    sell_nums = [(float(j) / 2).__ceil__() for j in chicang_nums]
    sell_cash = 0
    profit = 0
    data.loc[i, "chicang"] = ""
    for j in range(len(all_chicang)):
        data.loc[i, "sell_detail"] += (
            str(data.loc[i, "open"]) + ":" + str(sell_nums[j]) + ";"
        )
        sell_cash += data.loc[i, "open"] * sell_nums[j]
        data.loc[i, "chicang"] += (
            str(chicang_prices[j]) + ":" + str(chicang_nums[j] - sell_nums[j]) + ";"
        )
        profit += (data.loc[i, "open"] - chicang_prices[j]) * sell_nums[j]
    data.loc[i, "cash"] = data.loc[i, "cash"] + sell_cash
    data.loc[i, "profit"] = profit


def act_sell_2half(data, i):
    # 第二次卖点，就把所有的持仓都卖了。止盈和57分清仓可以复用
    if data.loc[i, "chicang"] == "":
        return
    all_chicang = data.loc[i, "chicang"].split(";")[0:-1]
    chicang_prices = [float(j.split(":")[0]) for j in all_chicang]
    chicang_nums = [float(j.split(":")[1]) for j in all_chicang]
    sell_nums = chicang_nums
    sell_cash = 0
    profit = 0
    data.loc[i, "chicang"] = ""
    for j in range(len(all_chicang)):
        data.loc[i, "sell_detail"] += (
            str(data.loc[i, "open"]) + ":" + str(sell_nums[j]) + ";"
        )
        sell_cash += data.loc[i, "open"] * sell_nums[j]
        # data.loc[i, 'chicang'] += str(chicang_prices[j]) + ':' + str(chicang_nums[j]-sell_nums[j]) + ';'
        profit += (data.loc[i, "open"] - chicang_prices[j]) * sell_nums[j]
    data.loc[i, "cash"] = data.loc[i, "cash"] + sell_cash
    data.loc[i, "profit"] = profit


def act_buy(data, i, first_cash, now_cash):
    buy_amt = first_cash // 2 // data.loc[i, "open"]
    if buy_amt * data.loc[i, "open"] > now_cash:
        buy_amt = now_cash // data.loc[i, "open"]
    if buy_amt >= 3:
        data.loc[i, "cash"] = data.loc[i, "cash"] - buy_amt * data.loc[i, "open"]
        data.loc[i, "chicang"] += str(data.loc[i, "open"]) + ":" + str(buy_amt) + ";"
        data.loc[i, "buy_detail"] += str(data.loc[i, "open"]) + ":" + str(buy_amt) + ";"
        data.loc[i, "max_zhiying_prices"] += str(data.loc[i, "open"]) + ";"


def act_init_1d(data, i, first_cash):
    data.loc[i, "cash"] = first_cash
    data.loc[i, "chicang"] = ""
    data.loc[i, "buy_detail"] = ""
    data.loc[i, "sell_detail"] = ""
    data.loc[i, "profit"] = 0
    data.loc[i, "max_zhiying_prices"] = ""


def act_init_1line(data, i):
    data.loc[i, "cash"] = data.loc[i - 1, "cash"]
    data.loc[i, "chicang"] = data.loc[i - 1, "chicang"]
    data.loc[i, "buy_detail"] = ""
    data.loc[i, "sell_detail"] = ""
    data.loc[i, "profit"] = 0
    data.loc[i, "max_zhiying_prices"] = data.loc[i - 1, "max_zhiying_prices"]
    # 计算止盈价格
    if data.loc[i, "max_zhiying_prices"] != "":
        max_zhiying_prices = [
            float(j) for j in data.loc[i, "max_zhiying_prices"].split(";")[0:-1]
        ]
        data.loc[i, "max_zhiying_prices"] = ""
        for k in range(len(max_zhiying_prices)):
            if float(data.loc[i, "open"] > max_zhiying_prices[k]):
                max_zhiying_prices[k] = data.loc[i, "open"]
            data.loc[i, "max_zhiying_prices"] += str(max_zhiying_prices[k]) + ";"


def huice_nd(code, n_atr, stg_ver):
    f_path = "./data_ready/"
    # code = "NVDA"
    # date = '20240417'
    # csv_path = os.path.join(f_path,code,date+'.csv')
    # atr = get_atr_longport("NVDA", "20231106")
    csvs = sorted(os.listdir(f_path + code))
    csvs_new = []
    for i in range(len(csvs)):
        # 只看2024年的
        if csvs[i].split(".")[0][0:4] == "2024":
            csvs_new.append(csvs[i])
    csvs = csvs_new
    csvs = [f_path + code + "/" + p for p in csvs]
    # 统计数据
    stat_track = {
        "code": code,
        "trade_days": 0,
        "win_days": 0,
        "win_sells": 0,
        "lose_sells": 0,
        "max_1d_profit": 0,
        "max_1d_lost": 0,
    }
    agent = longport_utils.Longport_agent()
    for i in range(len(csvs)):
        date = csvs[i].split("/")[-1].split(".")[0]
        data = pd.read_csv(csvs[i], index_col=0)
        # atr = get_atr_longport(code, date)
        jw = agent.get_jw_longport(code,date)
        # 过滤1D级别jw趋势向下，且高于某阈值时，不做多。
        if jw[-1]>80 and jw[-2]>jw[-1]:
            data["icon_1"],data["icon_38"],data["icon_34"],data["icon_13"],data["icon_11"]=0,0,0,0,0
        atr = 1

        if i == 0:
            # data_done, cash = huice_1d(data, 100000, round(atr / n_atr, 2))
            cash = 100000
            data_ops = ""

        data_done, cash = huice_1d(data, cash, n_atr)
        if (data_done.buy_signal.sum() > 0).any():
            data_op = data[
                (data.sell_detail != "")
                | (data.buy_detail != "")
                | (data.buy_signal > 0)
            ]
            if data_ops is "":
                data_ops = data_op.copy(deep=True)
            else:
                data_ops = pd.concat([data_ops, data_op])
            # 统计指标
            # buy_num = (data_op['buy_detail']!='').sum()
            # sell_num = (data_op['sell_detail']!='').sum()
            stat_track["trade_days"] += 1
            if data_op.profit.sum() > 0:
                stat_track["win_days"] += 1
                # stat_track['win_sells'] += (data_op.profit>0).sum()
            # stat_track['lose_sells'] += (data_op.profit < 0).sum()
            if stat_track["max_1d_profit"] < data_op.profit.sum():
                stat_track["max_1d_profit"] = data_op.profit.sum()
            if stat_track["max_1d_lost"] > data_op.profit.sum():
                stat_track["max_1d_lost"] = data_op.profit.sum()
        print(csvs[i])
        print(cash)
    stat_track["code"] = code
    stat_track["start_day"] = csvs[0].split("/")[-1].split(".")[0]
    stat_track["end_day"] = csvs[-1].split("/")[-1].split(".")[0]
    stat_track["start_cash"] = 100000
    stat_track["end_cash"] = data_ops.cash.iloc[-1]
    stat_track["total_profit_rate"] = (
        stat_track["end_cash"] / stat_track["start_cash"] - 1
    )
    stat_track["buy_nums"] = (data_ops.buy_detail != "").sum()
    stat_track["sell_nums"] = (data_ops.sell_detail != "").sum()
    stat_track["win_sells"] = (data_ops.profit > 0).sum()
    stat_track["lose_sells"] = (data_ops.profit < 0).sum()
    stat_track["avg_win_sell_profit"] = (
        data_ops[data_ops.profit > 0].profit.sum()
        / data_ops[data_ops.profit > 0].profit.count()
    )
    stat_track["avg_lose_sell_profit"] = (
        data_ops[data_ops.profit < 0].profit.sum()
        / data_ops[data_ops.profit < 0].profit.count()
    )

    # stg_ver = "3xatr_5min"
    save_folder = os.path.join(
        "./data_huice/", stg_ver
    )
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    # else:
    #     user_input = input(
    #         f"策略版本 '{stg_ver}' 已经存在. 是否替换? (yes/no): ").strip().lower()
    data_ops.to_csv(os.path.join(save_folder, code + ".csv"))
    pd.DataFrame(stat_track, index=[0]).T.to_csv(
        os.path.join(save_folder, code + "_stat.csv")
    )
    return stat_track


def huice_nd_threads(args):
    with multiprocessing.Pool(processes=8) as pool:
        # results=pool.map(huice_nd,args)
        results = pool.starmap(huice_nd, args)


def stat_huizong(root_folder):
    # root_folder = './data_huice/1.2x5min_atr/'
    csvs = sorted(os.listdir(root_folder))
    stat_csvs = []
    rets = []
    for csv in csvs:
        if 'stat' in csv:
            stat_csvs.append(csv)
    for csv in stat_csvs:
        df=pd.read_csv(root_folder+csv)
        df=df.T
        df.columns=df.iloc[0]
        rets.append([df['code'][1],float(df['total_profit_rate'][1])])
    df = pd.DataFrame(rets)
    df.columns=['code','total_profit_rate']
    df.loc[len(df)]=['平均',float(df['total_profit_rate'].mean())]
    df.to_csv(root_folder+'overall.csv')
    return df





if __name__ == "__main__":

    # huice_1d()
    # stat_track = huice_nd("TQQQ",9)
    # huice_nd_threads(["AMD","BABA","GOOGL","MSFT","PDD","TQQQ","TSLA","AAPL"])
    # huice_nd_threads(args=[["TQQQ"] + [i] for i in range(1, 8)])
    # huice_nd("AAPL",1,'debug')

    # 多线程回测
    # gps = ["TSLA", "PDD", "NVDA", "AAPL", "AMD", "BABA", "GOOGL", "MSFT",'QQQ']
    gps = ['TSLA', 'PDD', 'NVDA', 'AAPL', 'AMD', 'BABA', 'GOOGL', 'MSFT', 'QQQ']
    args = []
    stg_names = []

    for x_atr in np.arange(0.4, 0.5, 0.1):
        stg_name = str(round(float(x_atr), 2)) + "x5min_atr_jw1_qingcang_jw1d80"
        if stg_name not in stg_names:
            stg_names.append(stg_name)
        for gp in gps:
            args.append(
                [gp, round(float(x_atr), 2), stg_name]
            )
    huice_nd_threads(args)
    print("done!")
    for stg_name in stg_names:
        rf = './data_huice/'+stg_name+'/'
        stat_huizong(rf)
        print(rf+'回测统计完成')

