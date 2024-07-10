import numpy as np
from MyTT import *
import akshare as ak
import glob, os
import json
import pandas as pd
import math

class ZhiCheng:
    def const_1(self, X_in, Y, Z):
        if X_in == 0:
            X = CONST(SUM(IF(Y, REF(Z, 1), 0), 0))
            # DRAWNULL=0
            if X[-1] != 0:
                X_in = X[-1]
        else:
            X = np.array([X_in] * len(Y))
        return X, X_in

    def xinhao(self, C, L, H, V, CONST_dict):
        CLOSE = np.array(C)
        VOL = np.array(V)
        H = np.array(H)
        L = np.array(L)
        N = 5
        M = 15
        X_1 = CLOSE
        X_2 = SUM(CLOSE * VOL, 0) / SUM(VOL, 0)
        X_3 = SUM(CLOSE * VOL, 0) / SUM(VOL, 0)
        X_14 = REF(CLOSE, 1)
        X_15 = SMA(MAX(CLOSE - X_14, 0), 14, 1) / SMA(ABS(CLOSE - X_14), 14, 1) * 100
        X_16 = CROSS(80, X_15)
        X_17 = np.logical_and(FILTER(X_16, 60), CLOSE / X_3 > 1.005)

        X_18 = CROSS(X_15, 20)
        X_19 = np.logical_and(FILTER(X_18, 60), CLOSE / X_3 < 0.995)

        X_20 = np.logical_and(CLOSE > REF(CLOSE, 1), CLOSE / X_2 > 1 + N / 1000)
        X_21 = np.logical_and(CLOSE < REF(CLOSE, 1), CLOSE / X_2 < 1 - N / 1000)
        X_22 = CROSS(SUM(X_20, 0), 0.5)
        X_23 = CROSS(SUM(X_21, 0), 0.5)
        X_24 = np.array(SUM(X_22, 0)) * np.array(
            CROSS(COUNT(CLOSE < REF(CLOSE, 1), BARSLAST(X_22)[-1]), 0.5)
        )

        X_25 = SUM(X_23, 0) * CROSS(
            COUNT(CLOSE > REF(CLOSE, 1), BARSLAST(X_23)[-1]), 0.5
        )

        # X1=CONST(SUM(IF(X_24,REF(CLOSE,1),0),0)); #DRAWNULL=0
        X1, X1_in = self.const_1(CONST_dict["X1"], X_24, CLOSE)
        # Z1=CONST(SUM(IF(X_25,REF(CLOSE,1),0),0));
        Z1, Z1_in = self.const_1(CONST_dict["Z1"], X_25, CLOSE)
        X_26 = CROSS(SUM(np.logical_and(X_20, CLOSE > X1 * (1 + 1 / 100)), 0), 0.5)
        X_27 = CROSS(SUM(np.logical_and(X_21, CLOSE < Z1 * (1 - 1 / 100)), 0), 0.5)
        X_28 = SUM(X_26, 0) * CROSS(
            COUNT(CLOSE < REF(CLOSE, 1), BARSLAST(X_26)[-1]), 0.5
        )

        X_29 = SUM(X_27, 0) * CROSS(
            COUNT(CLOSE > REF(CLOSE, 1), BARSLAST(X_27)[-1]), 0.5
        )

        X2 = CONST(SUM(IF(X_28, REF(CLOSE, 1), 0), 0))
        # DRAWNULL=0
        Z2 = CONST(SUM(IF(X_29, REF(CLOSE, 1), 0), 0))
        # DRAWNULL=0
        X_30 = np.logical_and(CLOSE > REF(CLOSE, 1), CLOSE / X_2 > 1 + M / 1000)
        X_31 = np.logical_and(CLOSE < REF(CLOSE, 1), CLOSE / X_2 < 1 - M / 1000)
        X_32 = CROSS(SUM(X_30, 0), 0.5)
        X_33 = CROSS(SUM(X_31, 0), 0.5)
        X_34 = SUM(X_32, 0) * CROSS(
            COUNT(CLOSE < REF(CLOSE, 1), BARSLAST(X_32)[-1]), 0.5
        )
        X_35 = SUM(X_33, 0) * CROSS(
            COUNT(CLOSE > REF(CLOSE, 1), BARSLAST(X_33)[-1]), 0.5
        )
        # X_36=CONST(SUM(IF(X_34,REF(CLOSE,1),0),0)); #DRAWNULL=0
        X_36, X_36_in = self.const_1(CONST_dict["X_36"], X_34, CLOSE)
        # X_37=CONST(SUM(IF(X_35,REF(CLOSE,1),0),0));#DRAWNULL=0
        X_37, X_37_in = self.const_1(CONST_dict["X_37"], X_35, CLOSE)
        X_38 = CROSS(SUM(np.logical_and(X_30, CLOSE > X_36 * 1.02), 0), 0.5)
        X_39 = CROSS(SUM(np.logical_and(X_31, CLOSE < X_37 * 0.98), 0), 0.5)
        X_40 = SUM(X_38, 0) * CROSS(
            COUNT(CLOSE < REF(CLOSE, 1), BARSLAST(X_38)[-1]), 0.5
        )

        X_41 = SUM(X_39, 0) * CROSS(
            COUNT(CLOSE > REF(CLOSE, 1), BARSLAST(X_39)[-1]), 0.5
        )

        X_42 = CONST(SUM(IF(X_40, REF(CLOSE, 1), 0), 0))
        # DRAWNULL=0
        X_43 = CONST(SUM(IF(X_41, REF(CLOSE, 1), 0), 0))
        # DRAWNULL=0
        X_44 = np.logical_and(CLOSE > REF(CLOSE, 1), CLOSE / X_2 > 1 + 1 / 100)
        X_45 = np.logical_and(CLOSE < REF(CLOSE, 1), CLOSE / X_2 < 1 - 1 / 100)
        X_46 = CROSS(SUM(X_44, 0), 0.5)
        X_47 = CROSS(SUM(X_45, 0), 0.5)
        X_48 = SUM(X_46, 0) * CROSS(
            COUNT(CLOSE < REF(CLOSE, 1), BARSLAST(X_46)[-1]), 0.5
        )

        X_49 = SUM(X_47, 0) * CROSS(
            COUNT(CLOSE > REF(CLOSE, 1), BARSLAST(X_47)[-1]), 0.5
        )

        X_50 = CONST(SUM(IF(X_48, REF(CLOSE, 1), 0), 0))
        # DRAWNULL=0
        X_51 = CONST(SUM(IF(X_49, REF(CLOSE, 1), 0), 0))
        # DRAWNULL=0

        C = CLOSE

        V1 = (C * 2 + H + L) / 4 * 10
        V2 = EMA(V1, 13) - EMA(V1, 34)
        V3 = EMA(V2, 5)
        V4 = 2 * (V2 - V3) * 5.5

        dict = {
            "icon_1": int(X_25[-1]),
            "icon_2": int(X_24[-1]),
            "icon_11": int(X_41[-1]),
            "icon_12": int(X_40[-1]),
            "icon_13": int(X_19[-1]),
            "icon_41": int(X_17[-1]),
            "icon_34": int(X_29[-1]),
            "icon_35": int(X_28[-1]),
            "icon_38": int(X_49[-1]),
            "icon_39": int(X_48[-1]),
        }
        # 主力进WW=IF(V4>=0,V4,0);
        # V11=3*SMA((C-LLV(L,55))/(HHV(H,55)-LLV(L,55))*100,5,1)-2*SMA(SMA((C-LLV(L,55))/(HHV(H,55)-LLV(L,55))*100,5,1),3,1);
        # 趋势线=EMA(V11,3);
        # 见顶清仓=FILTER(np.logical_and(np.logical_and(趋势线>90, 趋势线<REF(趋势线,1)), 主力进WW<REF(主力进WW,1)),8);

        CONST_dict = {"X1": X1_in, "Z1": Z1_in, "X_36": X_36_in, "X_37": X_37_in}
        return dict, CONST_dict

    def xinhao_jw(self,C,L,H,V):
        N1 = 45;
        M1 = 15;
        M2 = 15;
        CLOSE = np.array(C)
        HIGH = np.array(H)
        LOW = np.array(L)
        RSV = (CLOSE - LLV(LOW, N1)) / (HHV(HIGH, N1) - LLV(LOW, N1)) * 100;
        K = SMA(RSV, M1, 1);
        D = SMA(K, M2, 1);
        JW = 3 * K - 2 * D;
        dict = {"jw": JW.tolist()}
        return dict

    def calc_jw(self,data):
        data_long = data.copy(deep=True)
        data_long.dt = pd.to_datetime(data_long.dt)
        data_long = data_long.reset_index(drop=True)
        open = data_long["open"].astype("float")
        close = data_long["close"].astype("float")
        high = data_long["high"].astype("float")
        low = data_long["low"].astype("float")
        volme = data_long["vol"].astype("float")
        time = data_long["dt"]
        res = self.xinhao_jw(close,low,high,volme)
        for k in res.keys():
            data_long[k] = res[k]
        return data_long


    def calc_point(self, data, date_mode="ib"):
        assert date_mode in ("ib", "tdx")
        if date_mode == "ib":  # ib的时间是正常的，过了24点dt会加一
            data.dt = pd.to_datetime(data.dt)
            '''
            debug筛选时间
            '''
            # threshold_date = pd.Timestamp('2024-05-01')
            # data = data[data.dt>=threshold_date]
            '''
            debug筛选时间
            '''
            date_list = sorted(data["dt"].dt.date.unique())
            for i in range(max(len(date_list) - 1,1)):  # 遍历所有输入data中的每个日期
                date_1d = str(date_list[i])
                date_1d_add1 = str(date_list[i + 1])
                print("正在计算", str(date_1d))
                data.dt = data.dt.astype("str")
                data_1d = data[
                    (
                        data["dt"].str.contains(date_1d)
                        & (data["dt"].str[11:13].astype(int) >= 20)
                    )
                    | (
                        data["dt"].str.contains(date_1d_add1)
                        & (data["dt"].str[11:13].astype(int) <= 4)
                    )
                ]
                data_1d = data_1d.reset_index(drop=True)
                open = data_1d["open"].astype("float")
                close = data_1d["close"].astype("float")
                high = data_1d["high"].astype("float")
                low = data_1d["low"].astype("float")
                volme = data_1d["vol"].astype("float")
                time = data_1d["dt"]
                CONST_dict = {"X1": 0, "Z1": 0, "X_36": 0, "X_37": 0}

                for j in range(len(open)):  # 遍历每一分钟
                    if j == 0:
                        continue
                    res, CONST_dict = self.xinhao(
                        close[0:j], low[0:j], high[0:j], volme[0:j], CONST_dict
                    )
                    # baixian = self.calc_baixian(close[0:j],low[0:j], high[0:j])
                    # res2 = self.xinhao_jw(close[0:j], low[0:j], high[0:j], volme[0:j])
                    for k in res.keys():
                        data_1d.loc[j, k] = res[k]
                    # data_1d.loc[j,'baixian']=baixian
                    # for k in res2.keys():
                    #     data_1d.loc[j,k] = res2[k]
                    if sum(res.values()) > 0:
                        print("time:", np.array(time)[j], res)
                if i == 0:
                    result = data_1d.copy()
                else:
                    result = pd.concat([result, data_1d], ignore_index=True)
            result.replace(0, np.nan, inplace=True)
        return result

    def calc_point_2_jw_1(self,ret):
        # debug使用
        ret.dt = pd.to_datetime(ret.dt)
        # data_jw5 = ret[ret['dt'].dt.minute.isin([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])]
        data_jw5 = ret.copy()
        data_jw5['group'] = data_jw5.index // 5
        data_jw5 = data_jw5.groupby('group').agg({'dt':'last','vol': 'sum', 'open': 'first', 'close': 'last','high':'max','low':'min'})
        # data_jw30 = ret[ret['dt'].dt.minute.isin([0, 30])]
        data_jw30 = ret.copy()
        data_jw30['group'] = data_jw30.index // 30
        data_jw30 = data_jw30.groupby('group').agg({'dt':'last','vol': 'sum', 'open': 'first', 'close': 'last','high':'max','low':'min'})
        ret1 = self.calc_jw(ret)
        ret5 = self.calc_jw(data_jw5)
        ret30 = self.calc_jw(data_jw30)
        jw1  =ret1[['dt', 'jw']].rename(columns={'jw': 'jw1'})
        jw5 = ret5[['dt', 'jw']].rename(columns={'jw': 'jw5'})
        jw30 = ret30[['dt', 'jw']].rename(columns={'jw': 'jw30'})
        merged = pd.merge(jw1, jw5[['dt', 'jw5']], on='dt', how='left')
        merged = pd.merge(merged, jw30[['dt', 'jw30']], on='dt', how='left')
        merged['jw5'].ffill(inplace=True)
        merged['jw30'].ffill(inplace=True)
        return merged

    def calc_baixian(self,ret):
        NA=80;
        M1A=19;
        M2A=3;
        CLOSE = ret["close"].astype("float")
        HIGH = ret["high"].astype("float")
        LOW = ret["low"].astype("float")
        ret.dt = pd.to_datetime(ret.dt)
        for j in range(len(CLOSE)):  # 遍历每一分钟
            if j == 0:
                continue
            RSV=(CLOSE[0:j]-LLV(LOW[0:j],NA))/(HHV(HIGH[0:j],NA)-LLV(LOW[0:j],NA))*100;
            K=SMA(RSV,M1A,1);
            D=SMA(K,M2A,1);
            NOTEXTDX=SMA(K,M2A,1);
            baijiao=math.atan((SMA(K,M2A,1)/REF(SMA(K,M2A,1),1)-1)[-1]*100)*180/3.1416;
            ret.loc[j,'baijiao'] = baijiao
        return ret


if __name__ == "__main__":
    ticker_symbol = "105.TSLA"
    # stock = ak.stock_us_hist_min_em(symbol=ticker_symbol)
    hist = ak.stock_us_hist_min_em(symbol=ticker_symbol)
    hist.columns = ["dt", "open", "close", "high", "low", "vol", "cje", "zxj"]
    zhicheng = ZhiCheng()
    ret = zhicheng.calc_point(hist, date_mode="ib")
    # ret2 = zhicheng.calc_point_2_jw_1(ret)
    # print(ret2)