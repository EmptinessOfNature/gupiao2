from macd_utils import tdx_raw2_kline,double_macd,jw,duanxian

def is_chuan_df(row,col,pre_len,post_len,thresh):
    index = row.name
    if index<pre_len+post_len-1:
        return False
    else:
        values_pre = data[col].iloc[index-pre_len-post_len+1:index-post_len+1]
        values_post = data[col].iloc[index-post_len+1:index+1]
        ret = bool(((values_pre<=thresh).all()) & ((values_post>thresh).all()))
        return ret

def merge_signal(data):
    # long_rules.append(
    #     data.loc[i, "m1"] > 0
    #     and abs(data.loc[i, "m1"]) > 1
    #     and is_chuan(data, i, "m2", 1, 1, "up", 0)
    #     and speed_abs(data, i, "m2", 2) > 0.1
    # )
    # long_rules.append(
    #     data.loc[i, "m1"] > 0
    #     and abs(data.loc[i, "m1"]) > 1
    #     and data.loc[i, "m2"] < 0
    #     and is_v(data, i, "m2", 3, 3, "bottom")
    #     and abs(data.loc[i, "m1"]) >= 2 * abs(data.loc[i, "m2"])
    # )
    data['debug_chuan'] = data.apply(is_chuan_df,axis=1,col='m1',pre_len=2,post_len=2,thresh=0)
    return data


if __name__=='__main__':
    code = 'TQQQ'
    data = tdx_raw2_kline("./data_tdx_raw/74#" + code + ".txt", period="390min")
    data = double_macd(data)
    data = jw(data)
    data = duanxian(data)
    data = merge_signal(data)
    print(1)