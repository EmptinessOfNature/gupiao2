import os.path

import pandas as pd
import numpy as np
import warnings
from buy_sell_point import ZhiCheng
import multiprocessing
from longport_utils import Longport_agent

warnings.filterwarnings("ignore")


def parse_tdx_rawdata_1d(r_path, code, w_path="./data_server/"):
    # 将通达信的原始数据解析为每一天的数据，存在文件夹中
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

    ret = df[["tdx_dt", "open", "close", "high", "low", "vol","turnover"]]
    ret["dt"] = pd.to_datetime(ret["tdx_dt"])

    def add_day_if_before_11(time):
        if time.hour <= 11:
            return time + pd.Timedelta(days=1)
        return time

    ret["dt"] = ret["dt"].apply(add_day_if_before_11)
    data = ret[["dt", "open", "close", "high", "low", "vol","turnover"]]

    date_list = sorted(data["dt"].dt.date.unique())
    for i in range(max(len(date_list) - 1, 1)):  # 遍历所有输入data中的每个日期
        date_1d = str(date_list[i])
        if int(date_1d[0:4])<2024 or int(date_1d[5:7])<8:
            continue
        date_1d_add1 = str(date_list[i + 1])
        data.dt = data.dt.astype("str")
        data_1d = data[
            (
                data["dt"].str.contains(date_1d)
                & (data["dt"].str[11:13].astype(int) >= 20)
            )
            | (
                data["dt"].str.contains(date_1d_add1)
                & (data["dt"].str[11:13].astype(int) <= 5)
            )
        ]
        data_1d = data_1d.reset_index(drop=True)
        data_1d["ts"] = (
            pd.to_datetime(data_1d["dt"], utc=False)
            .dt.tz_localize("Asia/Shanghai")
            .dt.tz_convert("utc")
            .astype("int64")
            / 10e8
        ).astype(int)
        if len(data_1d) > 0:
            assert len(data_1d) == 390
            if not os.path.exists(w_path + code):
                os.makedirs(w_path + code)
                print("新建文件夹", w_path + code)
            path_to_save = w_path + code + "/" + date_1d.replace("-", "") + ".csv"
            data_1d.to_csv(path_to_save)
            print(path_to_save, "保存完成")

def point_calc_hist_1d(code,f_path="./data_server/",w_path="./data_ready/"):
    def merge_data(req_data_list):
        ret = ""
        for file in req_data_list:
            try:
                if ret is "":
                    ret = pd.read_csv(file, index_col=0)
                else:
                    ret = pd.concat([ret, pd.read_csv(file, index_col=0)]).reset_index(drop=True)
            except:
                print(file, '本地不存在文件')
        return ret
    csvs = sorted(os.listdir(f_path+code))
    csvs = [f_path+code+'/'+p for p in csvs]
    for i in range(len(csvs)):
        data_lst5d = merge_data(csvs[max(0,i-5):i+1])
        data_lst2d = merge_data(csvs[max(0, i - 1):i + 1])
        data_1d = merge_data([csvs[i]])
        zhicheng = ZhiCheng()
        hist = zhicheng.calc_point(data_1d, date_mode="ib")
        hist['dt']=pd.to_datetime(hist['dt'])
        hist2 = zhicheng.calc_point_2_jw_1(data_lst5d)
        hist3 = hist2[-390:].reset_index(drop=True)
        hist4 = zhicheng.calc_baixian(data_lst2d)[-390:].reset_index(drop=True)
        # 计算日jw
        jw = zhicheng.agent.get_jw_longport(code=csvs[i].split('/')[-2], date=csvs[i].split('/')[-1].split('.')[0])[-1]

        if not os.path.exists(w_path + code):
            os.makedirs(w_path + code)
            print("新建文件夹", w_path + code)
        merged = pd.merge(hist, hist3, on='dt', how='left')
        merged = pd.merge(merged, hist4[['dt','baijiao','manxian']], on='dt', how='left')
        merged['jw1D'] = jw
        merged.to_csv(w_path+code+'/'+csvs[i].split('/')[-1])
        print(csvs[i],'计算完成')

def parse_tdx_rawdata_1d_threads(args):
    with multiprocessing.Pool(processes=8) as pool:
        # results=pool.map(huice_nd,args)
        results = pool.starmap(parse_tdx_rawdata_1d, args)

def point_calc_hist_1d_threads(args):
    with multiprocessing.Pool(processes=8) as pool:
        # results=pool.map(huice_nd,args)
        results = pool.starmap(point_calc_hist_1d, args)



if __name__ == "__main__":
    # 单线程debug
    # gp = 'TQQQ'
    # gps = ['QQQ']
    # for gp in gps:
    #     # parse_tdx_rawdata_1d(
    #     #     r_path="./data_tdx_raw/74#"+gp+".txt", code=gp, w_path="./data_server/"
    #     # )
    #     point_calc_hist_1d(code = gp)
    # print(1)
    # 多线程
    gps=['TSLA','PDD','NVDA','AAPL']

    args = []
    for gp in gps:
        args.append(["./data_tdx_raw/74#" + gp + ".txt", gp, "./data_server/"])
    parse_tdx_rawdata_1d_threads(args=args)

    args = []
    for gp in gps:
        args.append([gp,"./data_server/","./data_ready/"])
    point_calc_hist_1d_threads(args)

    gps = ['AMD','BABA','GOOGL','MSFT','QQQ']

    args = []
    for gp in gps:
        args.append(["./data_tdx_raw/74#" + gp + ".txt", gp, "./data_server/"])
    parse_tdx_rawdata_1d_threads(args=args)

    args = []
    for gp in gps:
        args.append([gp,"./data_server/","./data_ready/"])
    point_calc_hist_1d_threads(args)


