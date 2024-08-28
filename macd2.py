from macd_utils import tdx_raw2_kline,double_macd,jw,duanxian

def merge_signal(data):
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
    return data


if __name__=='__main__':
    code = 'TQQQ'
    data = tdx_raw2_kline("./data_tdx_raw/74#" + code + ".txt", period="390min")
    data = double_macd(data)
    data = jw(data)
    data = duanxian(data)
    print(1)