from time import sleep
import datetime
import numpy as np
from MyTT import *
from longport.openapi import QuoteContext, Config, SubType, PushQuote, Period, AdjustType
# def on_quote(symbol: str, quote: PushQuote):
#     print(symbol, quote)

def get_atr_longport(code,date):
    def get_date(date):
        y = int(date[0:4])
        m = int(date[4:6])
        d = int(date[6:8])
        for i in range(len(resp)):
            if resp[i].timestamp.replace(hour=12)==datetime.datetime(y, m, d, 12, 0):
                return i

    def get_atr(C, L, H):
        try:
            C = np.array(C)
            L = np.array(L)
            H = np.array(H)
            MTR = MAX(MAX((H - L), ABS(REF(C, 1) - H)), ABS(REF(C, 1) - L));
            ATR = MA(MTR, 14);
            return ATR[-1]
        except:
            print("atr 计算失败")

    config = Config(app_key = "307f42f17439c5557de1a8b6b3842cbd", app_secret = "0fcc0a1d198005adccd4856c5b888a93f93070ac52a97336848d3508808bf884", access_token = "m_eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb25nYnJpZGdlIiwic3ViIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzMwMTAxNjMyLCJpYXQiOjE3MjIzMjU2MzIsImFrIjoiMzA3ZjQyZjE3NDM5YzU1NTdkZTFhOGI2YjM4NDJjYmQiLCJhYWlkIjoyMDQxMDM3OSwiYWMiOiJsYl9wYXBlcnRyYWRpbmciLCJtaWQiOjEzNDcyODE5LCJzaWQiOiJyaHE3UlFENnZYWUtIbUU5TG0rWlZBPT0iLCJibCI6MywidWwiOjAsImlrIjoibGJfcGFwZXJ0cmFkaW5nXzIwNDEwMzc5In0.pYgn41BCyTOZbDqpqwUdqAnH_Ejein5k5V7rPYgvbtYAXqljPylaQVcUDKwkzwZgpgXP7IGWjJzBRLtCc2cnt56Ku35WAONPFmBy2xQh8AsHi7cJihiwiDmRJtUHBsFi5pzJOoql-luB7OOE_-4aswoXTzF9rFRIAniXN5GTibba-3yC08SnR3xH3a4MfzBTD0j3w5wT5lMPfEenF0YQL3IcKmM4SJDWqbbd_4WWYik6PbXXwhdOhnm0yKXCC8A79IRSBix6FB8oypbDS9LlPeBc71Cz7BVjpBWLynHSKqatMyexotVXtrRj0oP_99Kk2uviaaKB0eXmIbRhunv2QZJcFYKVUaSXfzYniEnD6Ns46QMski_EcZ3b0lA2g5QFKg4QO7f_D1dJqSoAeD19z9emSPzfPt5HI4Zo-2hbXAG5ItY3zORBF9qFR-qX_wDIKePL9yRigqOm9GoPXJnk_OxYW-pYSi4JFCV11-HG9n6NlIhOO8rEWs02iB65hfWQqg9BSPHHxawlnqMECZN-McGe5XhMMUleU-_qTHDv_U3Ugyf92G_fQQ1LLgkemO3nguBB5x66qxVIV_BpJ_l6DLTCS_g5HCgQD0qoAC2drEVvOpqvh_9v_5hGof891WvHwu4q27EbsNNBJ5qQg7pQk0vYf4WM9v6qSTftj1jeBFM")
    ctx = QuoteContext(config)
    code = code+'.US'
    resp = ctx.candlesticks(
        code, Period.Day, 400, AdjustType.NoAdjust)
    C=[]
    L=[]
    H=[]

    i=get_date(date)
    for j in range(i-15,i):
        C.append(float(resp[j].close))
        L.append(float(resp[j].low))
        H.append(float(resp[j].high))

    atr = get_atr(C,L,H)
    return atr

class Longport_agent():
    def __init__(self):
        config = Config(app_key = "307f42f17439c5557de1a8b6b3842cbd", app_secret = "0fcc0a1d198005adccd4856c5b888a93f93070ac52a97336848d3508808bf884", access_token = "m_eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb25nYnJpZGdlIiwic3ViIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzMwMTAxNjMyLCJpYXQiOjE3MjIzMjU2MzIsImFrIjoiMzA3ZjQyZjE3NDM5YzU1NTdkZTFhOGI2YjM4NDJjYmQiLCJhYWlkIjoyMDQxMDM3OSwiYWMiOiJsYl9wYXBlcnRyYWRpbmciLCJtaWQiOjEzNDcyODE5LCJzaWQiOiJyaHE3UlFENnZYWUtIbUU5TG0rWlZBPT0iLCJibCI6MywidWwiOjAsImlrIjoibGJfcGFwZXJ0cmFkaW5nXzIwNDEwMzc5In0.pYgn41BCyTOZbDqpqwUdqAnH_Ejein5k5V7rPYgvbtYAXqljPylaQVcUDKwkzwZgpgXP7IGWjJzBRLtCc2cnt56Ku35WAONPFmBy2xQh8AsHi7cJihiwiDmRJtUHBsFi5pzJOoql-luB7OOE_-4aswoXTzF9rFRIAniXN5GTibba-3yC08SnR3xH3a4MfzBTD0j3w5wT5lMPfEenF0YQL3IcKmM4SJDWqbbd_4WWYik6PbXXwhdOhnm0yKXCC8A79IRSBix6FB8oypbDS9LlPeBc71Cz7BVjpBWLynHSKqatMyexotVXtrRj0oP_99Kk2uviaaKB0eXmIbRhunv2QZJcFYKVUaSXfzYniEnD6Ns46QMski_EcZ3b0lA2g5QFKg4QO7f_D1dJqSoAeD19z9emSPzfPt5HI4Zo-2hbXAG5ItY3zORBF9qFR-qX_wDIKePL9yRigqOm9GoPXJnk_OxYW-pYSi4JFCV11-HG9n6NlIhOO8rEWs02iB65hfWQqg9BSPHHxawlnqMECZN-McGe5XhMMUleU-_qTHDv_U3Ugyf92G_fQQ1LLgkemO3nguBB5x66qxVIV_BpJ_l6DLTCS_g5HCgQD0qoAC2drEVvOpqvh_9v_5hGof891WvHwu4q27EbsNNBJ5qQg7pQk0vYf4WM9v6qSTftj1jeBFM")
        self.ctx = QuoteContext(config)
    def get_data_1D(self,code):
        code = code+'.US'
        resp = self.ctx.candlesticks(
            code, Period.Day, 800, AdjustType.NoAdjust)
        return resp

if __name__=='__main__':
    # print(get_atr_longport('NVDA','20240417'))
    agent = Longport_agent()
    resp = agent.get_data_1D('TQQQ')
    print(1)