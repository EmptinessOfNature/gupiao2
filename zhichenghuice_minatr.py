import pandas as pd
import os
import numpy as np
import multiprocessing
from MyTT import *
from longport_utils import get_atr_longport
from datetime import datetime


def huice_1d(data, first_cash, zhiying_diff):
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
        zhiying_diff = data.loc[i,'atr5'] * 3
        if i == 0:
            act_init_1d(data, i, first_cash)
            sell_no_mod_2 = 0
        else:
            act_init_1line(data, i)
        if data.loc[i, "buy_signal"] == 1 and i < 389 - 3:
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


def huice_nd(code, atr_div_rate):
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
    for i in range(len(csvs)):
        date = csvs[i].split("/")[-1].split(".")[0]
        data = pd.read_csv(csvs[i], index_col=0)
        # atr = get_atr_longport(code, date)
        atr=1
        if i == 0:
            # data_done, cash = huice_1d(data, 100000, round(atr / atr_div_rate, 2))
            cash = 100000
            data_ops = ""

        # else:
        data_done, cash = huice_1d(data, cash, round(atr / atr_div_rate, 2))
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

    stg_ver = "3xatr_5min"
    save_folder = os.path.join(
        "./data_huice/", stg_ver , datetime.now().strftime("%Y%m%d%H%M")
    )
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    # else:
    #     user_input = input(
    #         f"策略版本 '{stg_ver}' 已经存在. 是否替换? (yes/no): ").strip().lower()
    data_ops.to_csv(os.path.join(save_folder, code + ".csv"))
    pd.DataFrame(stat_track, index=[0]).T.to_csv(
        os.path.join(save_folder, code + "_统计数据.csv")
    )
    return stat_track


def huice_nd_threads(args):
    with multiprocessing.Pool(processes=8) as pool:
        # results=pool.map(huice_nd,args)
        results = pool.starmap(huice_nd, args)


if __name__ == "__main__":
    # huice_1d()
    # stat_track = huice_nd("TQQQ",9)
    # huice_nd_threads(["AMD","BABA","GOOGL","MSFT","PDD","TQQQ","TSLA","AAPL"])
    # huice_nd_threads(args=[["TQQQ"] + [i] for i in range(1, 8)])
    # huice_nd("TQQQ",1)
    gps = ['TSLA', 'PDD', 'NVDA', 'AAPL', 'AMD', 'BABA', 'GOOGL', 'MSFT']
    args=[]
    for gp in gps:
        args.append([gp,1])
    huice_nd_threads(args)
    print("done!")
