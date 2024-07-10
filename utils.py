import os.path

import pandas as pd
import numpy as np
import warnings
from buy_sell_point import ZhiCheng

warnings.filterwarnings("ignore")


def parse_tdx_rawdata_1d(r_path, code, w_path="./data_server/"):
    # 将通达信的原始数据解析为每一天的数据，存在文件夹中
    df = pd.read_csv(r_path, sep="\t", skiprows=1, encoding="gbk")[:-1]
    df.columns = ["date", "time", "open", "high", "low", "close", "vol", "cje"]
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

    ret = df[["tdx_dt", "open", "close", "high", "low", "vol"]]
    ret["dt"] = pd.to_datetime(ret["tdx_dt"])

    def add_day_if_before_11(time):
        if time.hour <= 11:
            return time + pd.Timedelta(days=1)
        return time

    ret["dt"] = ret["dt"].apply(add_day_if_before_11)
    data = ret[["dt", "open", "close", "high", "low", "vol"]]

    date_list = sorted(data["dt"].dt.date.unique())
    for i in range(max(len(date_list) - 1, 1)):  # 遍历所有输入data中的每个日期
        date_1d = str(date_list[i])
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
    for i in range(500,len(csvs)):
        data_lst5d = merge_data(csvs[max(0,i-5):i+1])
        data_lst2d = merge_data(csvs[max(0, i - 1):i + 1])
        data_1d = merge_data([csvs[i]])
        zhicheng = ZhiCheng()
        hist = zhicheng.calc_point(data_1d, date_mode="ib")
        hist['dt']=pd.to_datetime(hist['dt'])
        hist2 = zhicheng.calc_point_2_jw_1(data_lst5d)
        hist3 = hist2[-390:].reset_index(drop=True)
        hist4 = zhicheng.calc_baixian(data_lst2d)[-390:].reset_index(drop=True)

        if not os.path.exists(w_path + code):
            os.makedirs(w_path + code)
            print("新建文件夹", w_path + code)
        merged = pd.merge(hist, hist3, on='dt', how='left')
        merged = pd.merge(merged, hist4[['dt','baijiao']], on='dt', how='left')
        merged.to_csv(w_path+code+'/'+csvs[i].split('/')[-1])
        print(csvs[i],'计算完成')





if __name__ == "__main__":
    # gp = 'TQQQ'
    # gps=['TSLA','PDD','NVDA','AAPL']
    # gps=['AMD','BABA','GOOGL','MSFT']
    gps = ['MSFT']
    for gp in gps:
        parse_tdx_rawdata_1d(
            r_path="./data_tdx_raw/74#"+gp+".txt", code=gp, w_path="./data_server/"
        )
        point_calc_hist_1d(code = gp)
    # print(1)
