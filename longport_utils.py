from time import sleep
import datetime
from longport.openapi import QuoteContext, Config, SubType, PushQuote
def on_quote(symbol: str, quote: PushQuote):
    print(symbol, quote)
config = Config(app_key = "605e162381fc6cfe573d0a1dff24e610", app_secret = "4b5f05d13ca8e65dc4c6a51c40144d0e7473c1762d32f8a70c4d73d8757ed4b2", access_token = "m_eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb25nYnJpZGdlIiwic3ViIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzI4MDI5MzM0LCJpYXQiOjE3MjAyNTMzMzksImFrIjoiNjA1ZTE2MjM4MWZjNmNmZTU3M2QwYTFkZmYyNGU2MTAiLCJhYWlkIjoyMDI5NTYwOSwiYWMiOiJsYl9wYXBlcnRyYWRpbmciLCJtaWQiOjExODk2MTg4LCJzaWQiOiJ1Z1Z4am5ETk1hR2lqTFJsbjNCbCt3PT0iLCJibCI6MywidWwiOjAsImlrIjoibGJfcGFwZXJ0cmFkaW5nXzIwMjk1NjA5In0.OBSJcR7Sli0iqo9HeM47hYqWXTVj_D-Kq2CcZJ4epzRByP74uaLNu4vSWeCwJX7ehZBWHcTQU35kAbJbhrKictyUa43X6bXGLsAmYsgTO7f2O3HKQTOCfb221EUxXjxftkT-9nj4qPqx3SC8Kdn7LGhbeQO_k2OQjVfmpGex3TOy0_Bukj7wQfp8ybgp_MPgadlfQqXyi2g4bS7G6lM9Ln9DifJVpeqHR0mc2Cv4kT_G3wnaWm7gwVOkM3m9UvIAqFvARkQLSFeLAmadHi4ohleRgGW-JzCK9B9ITWK15DqHWBjSJd9iq-G1z6qDrtU0lDQC2IugjwrVI2ishoDeqEBzOoml4y8W9bUCf69GCWaeW9_8HU2XHsjUjAlXr7G82CShYNJxTayXafkQr9DriFqDzilUzxADHvfxclO1VesqmYVHWWUxQf-N87UqsHbRiKS5vtM31UHAaPI8VUh3-bqYgvfovpw8m031vckvmQ0nfLH9fWQEwiy8bFUR1YnQZpw1OmDdQCn5L-gYzHgDgqEg2WMtuKiZNcbvfuc5LFCYyLCZQGKhR3X_3kL3a5G900N7-E295mNIxf8Q2MyLLKS3bmuasFMwUkyXRbeyzjeuUpRmKvTt3XNk4iGD8aqmFWGm9J5XdRS0wqf6bXWwQS4VQPk1QEH1Q_4ppA1K15o")

# ctx = QuoteContext(config)
# ctx.set_on_quote(on_quote)
# symbols = ["700.HK", "AAPL.US", "TSLA.US", "NFLX.US"]
# ctx.subscribe(symbols, [SubType.Quote],False)
# sleep(30)
# ctx.unsubscribe(symbols, [SubType.Quote])

from longport.openapi import QuoteContext, Config, Period, AdjustType

ctx = QuoteContext(config)

resp = ctx.candlesticks(
    "NVDA.US", Period.Day, 1000, AdjustType.NoAdjust)
print(resp)

C=[]
L=[]
H=[]
def get_date():
    for i in range(len(resp)):
        if resp[i].timestamp==datetime.datetime(2024, 7, 11, 12, 0):
            return i
i=get_date()
for j in range(i-14,i):
    C.append(float(resp[j].close))
    L.append(float(resp[j].low))
    H.append(float(resp[j].high))

print(1)
