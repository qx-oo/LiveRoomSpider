# LiveRoomSpider

爬去直播间状态，支持斗鱼，战旗，熊猫

使用方法:
```
async def testfunc():
    result = await LiveRoomSpider('https://www.panda.tv/xxxxx').get_result()
    print(result)
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([testfunc()]))
```

支持python3.4+
