from liveroom_spider.spider import LiveRoomSpider
import asyncio


if __name__ == '__main__':
    async def testfunc():
        result = await LiveRoomSpider('https://www.panda.tv/xxxxx').get_result()
        print(result)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([testfunc()]))
