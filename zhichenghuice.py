import pandas as pd
import os
import numpy as np
from MyTT import *
from longport_utils import get_atr_longport

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
        if i == 0:
            act_init_1d(data, i, first_cash)
            sell_no_mod_2 = 0
        else:
            act_init_1line(data, i)
        if data.loc[i, "buy_signal"] == 1:
            act_buy(data, i, first_cash)
            print(1)
        if data.loc[i, "sell_signal"] == 1:
            if sell_no_mod_2 == 0:
                act_sell_1half(data, i)
                print(1)
            else:
                act_sell_2half(data, i)
                print(1)
            sell_no_mod_2 = 1 - sell_no_mod_2
        max_zhiying_prices = [
            float(j) for j in data.loc[i, "max_zhiying_prices"].split(";")[0:-1]
        ]
        if (
            np.array(max_zhiying_prices) - float(data.loc[i, "open"]) >= zhiying_diff
        ).any():
            act_sell_zhiying(data, i, zhiying_diff)
            print(1)
        if i == 389 - 3:
            act_sell_2half(data, i)


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
            data.loc[i,'max_zhiying_prices']+= (
                str(max_zhiying_prices[j]) + ";"
            )


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


def act_buy(data, i, first_cash):
    buy_amt = first_cash // 2 // data.loc[i, "open"]
    if buy_amt >= 1:
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


if __name__ == "__main__":
    f_path = "./data_ready/"
    code = "NVDA"
    date = '20240417'
    csv_path = os.path.join(f_path,code,date+'.csv')
    csvs = sorted(os.listdir(f_path + code))
    csvs = [f_path + code + "/" + p for p in csvs]
    data = pd.read_csv(csv_path, index_col=0)
    atr = get_atr_longport(code,date)
    huice_1d(data, 100000,round(atr/8,2))
    print(1)
    # debug
    # for csv in csvs:
    #     data = pd.read_csv(csv, index_col=0)
    #     icon_buy = (
    #         (
    #             data["icon_1"].fillna(0)
    #             + data["icon_38"].fillna(0)
    #             + data["icon_34"].fillna(0)
    #             + data["icon_13"].fillna(0)
    #             + data["icon_11"].fillna(0)
    #         )
    #         >= 1
    #     ).astype(int)
    #     icon_jw5_30_bottom = (
    #         ((data["jw5"] < 20).astype(int) + (data["jw30"] < 20).astype(int)) >= 2
    #     ).astype(int)
    #     icon_sell = (
    #         (
    #             data["icon_2"].fillna(0)
    #             + data["icon_39"].fillna(0)
    #             + data["icon_35"].fillna(0)
    #             + data["icon_12"].fillna(0)
    #             + data["icon_41"].fillna(0)
    #         )
    #         >= 1
    #     ).astype(int)
    #     icon_jw5_30_top = (
    #         ((data["jw5"] > 80).astype(int) + (data["jw30"] > 80).astype(int)) >= 2
    #     ).astype(int)
    #
    #     data["buy_signal"] = icon_jw5_30_bottom * icon_buy
    #     data["sell_signal"] = icon_sell
    #     if data["buy_signal"].sum() >= 1: #and data["sell_signal"].sum() >= 1:
    #         print(csv)
    #         print(icon_sell.sum())