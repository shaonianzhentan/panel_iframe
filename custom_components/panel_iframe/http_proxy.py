import aiohttp, asyncio
from aiohttp import web
from urllib.parse import urlparse

class HttpProxy:

    def __init__(self, url: str):
        parsed_url = urlparse(url)
        route_path = parsed_url.path.strip('/')
        
        if route_path == '':
            route_path = parsed_url.netloc.replace(':', '').replace('.', '')
            self.is_root = True
        else:
            self.is_root = False
        self.proxy_host = parsed_url.netloc
        self.proxy_path = route_path

    def register(self, router):
        ''' 路由注册 '''
        route_url = f'/{self.proxy_path}/' + '{tail:.*}'
        # print(route_url)
        router.add_route('*', route_url, self.handler)

    def get_url(self, hostname=''):
        ''' 获取访问地址 '''
        return f'{hostname}/{self.proxy_path}/'

    def get_path(self, request):
        ''' 获取真实路径地址 '''
        url_path = request.rel_url.path
        if self.is_root:
            url_path = url_path.replace(f'/{self.proxy_path}', '')
        return url_path

    async def handler(self, request):
        target_ws = f'ws://{self.proxy_host}'
        target_http = f'http://{self.proxy_host}'
        if request.headers.get('Upgrade', '').lower() == 'websocket':
            return await self.websocket_handler(request, target_ws)
        else:
            return await self.http_handler(request, target_http)

    async def http_handler(self, request, target_url):

        target = target_url + self.get_path(request)
        if request.query_string:
            target += '?' + request.query_string

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=target,
                headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
                data=await request.read()
            ) as resp:
                headers = {k: v for k, v in resp.headers.items() if k.lower() != 'transfer-encoding'}
                body = await resp.read()
                return web.Response(body=body, status=resp.status, headers=headers)

    async def websocket_handler(self, request, target_url):
        ws_server = web.WebSocketResponse()
        await ws_server.prepare(request)

        target = target_url + self.get_path(request)
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(target) as ws_client:
                async def ws_forward(ws_from, ws_to):
                    async for msg in ws_from:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await ws_to.send_str(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            await ws_to.send_bytes(msg.data)
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            await ws_to.close()

                await asyncio.gather(ws_forward(ws_server, ws_client), ws_forward(ws_client, ws_server))

        return ws_server