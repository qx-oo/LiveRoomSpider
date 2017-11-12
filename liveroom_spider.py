# -*- coding: utf-8 -*-

# version: 1.0
# author: shawn

from lxml import etree
import re
import aiohttp
import json


class LiveRoomSpider():
    '''
    直播间爬虫
    '''

    def __init__(self, url):
        '''
        self.result = {
            'source_url': self.url,
            'active': False,
            'liveroom_name': '',
            'liveer_name': '',
            'live_thumbnail': '',
            'audience_count': 0,
            'liveer_avatar': '',
        }
        '''
        self.site_func = {
            '.*\.douyu\.com.*': self.douyu_func_spider,
            '.*\.panda\.tv.*': self.panda_func_spider,
            '.*\.zhanqi\.tv.*': self.zhanqi_func_spider,
            '.*\.bilibili.com.*': self.bilibili_func_spider,
        }
        self.url = url
        self.result = {}

    async def get_result(self, validate=False):
        '''
        '''
        for site, func in self.site_func.items():
            p = re.compile(site)
            if p.match(self.url):
                await func()
        if validate:
            for key, value in self.result.items():
                if not value and key != 'active':
                    return {}
        return self.result

    async def bilibili_func_spider(self):
        '''
        哔哩哔哩直播解析
        '''
        self.result['live_platform'] = "哔哩哔哩"
        try:
            room_id = re.findall('\.bilibili.com/.*?(\d*)$', self.url)
            if not room_id:
                return
            response = await self.get_response("https://api.live.bilibili.com/AppRoom/index?platform=ios&room_id=%s" % room_id[0])
        except Exception as e:
            return
        data = json.loads(response)
        if data.get('data'):
            self.result['live_thumbnail'] = data['data'].get('cover', '')
            self.result['liveroom_name'] = data['data'].get('title', '')
            self.result['liveer_name'] = data['data'].get('uname', '')
            self.result['liveer_avatar'] = data['data'].get('face', '')

            # PREPARING 是闲置的, ROUND是轮播, LIVE是直播
            self.result['active'] = (data['data'].get('status', 'PREPARING') == "LIVE")
            try:
                self.result['audience_count'] = int(data['data'].get('online', 0))
            except ValueError:
                self.result['audience_count'] = 0

    async def zhanqi_func_spider(self):
        '''
        战旗直播网页解析
        '''
        self.result['live_platform'] = '战旗'
        try:
            room_id = re.findall('\.zhanqi\.tv/(.*)$', self.url)
            if not room_id:
                return
            response = await self.get_response('https://m.zhanqi.tv/api/static/v2.1/room/domain/%s.json' % room_id[0])
        except Exception as e:
            return
        data = json.loads(response)
        if data.get('data'):
            self.result['live_thumbnail'] = data['data'].get('spic', '')
            self.result['active'] = True
            self.result['liveroom_name'] = data['data'].get('title', '')
            self.result['liveer_name'] = data['data'].get('nickname', '')
            self.result['liveer_avatar'] = data['data'].get('avatar', '')
            try:
                self.result['audience_count'] = int(data['data'].get('online', 0))
            except ValueError:
                self.result['audience_count'] = 0

    async def panda_func_spider(self):
        '''
        熊猫直播网页解析
        '''
        self.result['live_platform'] = '熊猫'
        try:
            room_id = re.findall('\.panda\.tv/.*?(\d*)$', self.url)
            if not room_id:
                return
            response = await self.get_response('https://room.api.m.panda.tv/index.php?method=room.shareapi&roomid=%s' % room_id[0])
        except Exception as e:
            return
        data = json.loads(response)
        if data.get('data'):
            self.result['active'] = False
            if data['data'].get('hostinfo'):
                self.result['liveer_name'] = data['data']['hostinfo'].get('name', '')
                self.result['liveer_avatar'] = data['data']['hostinfo'].get('avatar', '')
            if data['data'].get('roominfo'):
                self.result['liveroom_name'] = data['data']['roominfo'].get('name', '')
                self.result['live_thumbnail'] = data['data']['roominfo'].get('pictures', {}).get('img', '')
                try:
                    self.result['audience_count'] = int(data['data']['roominfo'].get('person_num'))
                except ValueError:
                    self.result['audience_count'] = 0
            if data['data'].get('videoinfo', {}).get('address', ''):
                self.result['active'] = True

    async def douyu_func_spider(self):
        '''
        斗鱼直播网页解析
        '''
        self.result['live_platform'] = '斗鱼'
        try:
            url = self.url.replace('www.douyu.com', 'm.douyu.com')
            response = await self.get_response(url)
        except Exception as e:
            return
        active_str = re.findall(r'isLive\s*:\s*(\d)\s*,', response)
        if active_str:
            self.result['active'] = True if active_str[0] == '1' else False
        if not self.result['active']:
            return
        room_id = re.findall(r'room_id\s*:\s*(\d*)\s*,', response)
        if room_id:
            room_id = room_id[0]
        else:
            return
        # parse liveroom_name and live_thumbnail
        liveroom_name_str = re.findall(r'roomName\s*:\s*"(.*)"\s*,', response)
        if liveroom_name_str:
            self.result['liveroom_name'] = liveroom_name_str[0]
        live_thumbnail_str = re.findall(r'roomSrc\s*:\s*"(.*)"\s*,', response)
        if live_thumbnail_str:
            self.result['live_thumbnail'] = live_thumbnail_str[0]

        # parse liveer name and audience count
        try:
            response = await self.get_response('https://m.douyu.com/video/getList?rid=%s' % room_id)
        except Exception as e:
            return
        data = json.loads(response)
        if data.get('data'):
            if data['data'].get('roomInfo'):
                self.result['liveer_name'] = data['data']['roomInfo'].get('nickname', '')
                self.result['liveer_avatar'] = data['data']['roomInfo'].get('avatar', '')
                audience_str = data['data']['roomInfo'].get('online')
                try:
                    self.result['audience_count'] = int(float(audience_str))
                except ValueError:
                    self.result['audience_count'] = int(float(audience_str.replace('万', '')) * 10000)

    async def get_response(self, url):
        '''
        异步请求
        '''
        response = None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response = await response.read()
                if isinstance(response, bytes):
                    response = response.decode('utf8')
        return response
