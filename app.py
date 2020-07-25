import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


from MyAsyncHttp import Server,Request
from MyAsyncHttp import async_io

server = Server('127.0.0.1', 8000)

@server.router.rule("/", method="GET")
def index(request: Request):
    import time
    time.sleep(0)
    return "welcome to index"

@server.router.rule("/hello", method="GET")
def hello(request: Request):
    name = request.params['name']
    return "hello," + name

@server.router.rule("/baidu", method="GET")
def baidu(request: Request):
    url = "http://www.baidu.com"
    res_header, res_body = yield from async_io.http_request.request("GET", url, header=[])
    return res_body


server.start()