from macd_utils import tdx_raw2_kline,double_macd,jw,duanxian

def is_chuan(data,col,pre_len,post_len,thresh,direction):
    def _is_chuan_up(row,col,pre_len,post_len,thresh):
        index = row.name
        if index<pre_len+post_len-1:
            return False
        else:
            values_pre = data[col].iloc[index-pre_len-post_len+1:index-post_len+1]
            values_post = data[col].iloc[index-post_len+1:index+1]
            ret = bool(((values_pre<=thresh).all()) & ((values_post>thresh).all()))
            return ret
    def _is_chuan_down(row,col,pre_len,post_len,thresh):
        index = row.name
        if index<pre_len+post_len-1:
            return False
        else:
            values_pre = data[col].iloc[index-pre_len-post_len+1:index-post_len+1]
            values_post = data[col].iloc[index-post_len+1:index+1]
            ret = bool(((values_pre>=thresh).all()) & ((values_post<thresh).all()))
            return ret
    if direction=='up':
        ret = data.apply(_is_chuan_up, axis=1, col=col, pre_len=pre_len, post_len=post_len, thresh=thresh)
    elif direction=='down':
        ret = data.apply(_is_chuan_down, axis=1, col=col, pre_len=pre_len, post_len=post_len, thresh=thresh)
    else:
        raise ValueError("direction错误")
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
    data['is_chuan_up']  = is_chuan(data,col='m1',pre_len=2,post_len=2,thresh=0,direction='up')
    data['is_chuan_down'] = is_chuan(data,col='m1',pre_len=2,post_len=2,thresh=0,direction='down')
    # 规则1
    (data['m1']>0) & (data['m1'].abs()>1)
    return data


if __name__=='__main__':
    code = 'TQQQ'
    data = tdx_raw2_kline("./data_tdx_raw/74#" + code + ".txt", period="390min")
    data = double_macd(data)
    data = jw(data)
    data = duanxian(data)
    data = merge_signal(data)
    print(1)