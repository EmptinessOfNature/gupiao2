def calc_buy_sell_point(data, stg_ver="1"):
    # 判断是否是v形
    def is_v(data, i, col, pre_length, post_length, direction):
        if i < pre_length + post_length:
            return False
        i_seq = list(range(i - pre_length - post_length, i + 1))
        diffs = np.array(
            data.loc[i_seq, col].diff().reset_index(drop=True).drop(index=0)
        )
        if (
            direction == "bottom"
            and (diffs[0:pre_length] < 0).all()
            and (diffs[pre_length : pre_length + post_length] > 0).all()
        ):
            return True

        if (
            direction == "top"
            and (diffs[0:pre_length] > 0).all()
            and (diffs[pre_length : pre_length + post_length] < 0).all()
        ):
            return True
        return False

    # 判断是否穿0轴
    def is_chuan(data, i, col, pre_length, post_length, direction, thresh):
        if i < pre_length + post_length:
            return False
        i_seq = list(range(i - pre_length - post_length, i + 1))
        ret = np.array(data.loc[i_seq, col].reset_index(drop=True))
        if (
            direction == "up"
            and (ret[0:pre_length] < thresh).all()
            and (ret[pre_length : pre_length + post_length] > thresh).all()
        ):
            return True
        if (
            direction == "down"
            and (ret[0:pre_length] > thresh).all()
            and (ret[pre_length : pre_length + post_length] < thresh).all()
        ):
            return True
        return False

    data["long"] = 0
    data["short"] = 0
    data["long_stop"] = 0
    data["short_stop"] = 0
    for i in range(len(data)):
        # 做多开单条件，多个append的条件是或的关系，下同
        long_rules = []
        long_stop_rules = []
        short_rules = []
        short_stop_rules = []
        # 策略版本1，TQQQ收益率60%，MSFT收益率32%
        if stg_ver == "1":
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
            # 做多止盈止损条件

            long_stop_rules.append(is_chuan(data, i, "m2", 1, 1, "down", 0))
            long_stop_rules.append(is_v(data, i, "m2", 3, 3, "top"))
            long_stop_rules.append(speed_abs(data, i, "m2", 2) < 0.01)

            # 做空开单条件

            short_rules.append(
                data.loc[i, "m1"] < 0
                and abs(data.loc[i, "m1"]) > 1
                and is_chuan(data, i, "m2", 1, 1, "down", 0)
                and speed_abs(data, i, "m2", 2) > 0.1
            )
            short_rules.append(
                data.loc[i, "m1"] < 0
                and abs(data.loc[i, "m1"]) > 1
                and data.loc[i, "m2"] > 0
                and is_v(data, i, "m2", 3, 3, "top")
                and abs(data.loc[i, 'm2']) > 0.5
                and abs(data.loc[i, "m1"]) >= 2 * abs(data.loc[i, "m2"])
            )
            # 做空止盈止损条件

            short_stop_rules.append(is_chuan(data, i, "m2", 1, 1, "up", 0))
            short_stop_rules.append(is_v(data, i, "m2", 3, 3, "bottom"))
            short_stop_rules.append(speed_abs(data, i, "m2", 2) < 0.01)
        # 策略版本2，增加开仓时候m1方向的判断
        if stg_ver == "2":
            long_rules.append(
                data.loc[i, "m1"] > 0
                and abs(data.loc[i, "m1"]) > 1
                and is_chuan(data, i, "m2", 1, 1, "up", 0)
                and speed_abs(data, i, "m2", 2) > 0.1
                # and speed(data,i,'m1',3)>0
            )
            long_rules.append(
                data.loc[i, "m1"] > 0
                and abs(data.loc[i, "m1"]) > 1
                and data.loc[i, "m2"] < 0
                and is_v(data, i, "m2", 3, 3, "bottom")
                and abs(data.loc[i, 'm2']) > 0.5
                and abs(data.loc[i, "m1"]) >= 2 * abs(data.loc[i, "m2"])
                # and speed(data, i, 'm1', 3) > 0
            )
            # 做多止盈止损条件

            long_stop_rules.append(is_chuan(data, i, "m2", 1, 1, "down", 0))
            long_stop_rules.append(is_v(data, i, "m2", 3, 3, "top"))
            long_stop_rules.append(speed_abs(data, i, "m2", 2) < 0.01)

            # 做空开单条件

            short_rules.append(
                data.loc[i, "m1"] < 0
                and abs(data.loc[i, "m1"]) > 1
                and is_chuan(data, i, "m2", 1, 1, "down", 0)
                and speed_abs(data, i, "m2", 2) > 0.1
                # and speed(data, i, 'm1', 3) < -0
            )
            short_rules.append(
                data.loc[i, "m1"] < 0
                and abs(data.loc[i, "m1"]) > 1
                and data.loc[i, "m2"] > 0
                and is_v(data, i, "m2", 3, 3, "top")
                and abs(data.loc[i, "m1"]) >= 2 * abs(data.loc[i, "m2"])
                # and speed(data, i, 'm1', 3) < -0
            )
            # 做空止盈止损条件

            short_stop_rules.append(is_chuan(data, i, "m2", 1, 1, "up", 0))
            short_stop_rules.append(is_v(data, i, "m2", 3, 3, "bottom"))
            short_stop_rules.append(speed_abs(data, i, "m2", 2) < 0.01)

        if i <= 2:
            continue
        # 做多
        if sum(long_rules) > 0:
            data.loc[i, "long"] = 1
        # 做空
        if sum(short_rules) > 0:
            data.loc[i, "short"] = 1
        # 多单了结
        if sum(long_stop_rules) > 0:
            data.loc[i, "long_stop"] = 1
        # 空单了结
        if sum(short_stop_rules) > 0:
            data.loc[i, "short_stop"] = 1

    return data
