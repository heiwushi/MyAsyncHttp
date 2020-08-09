# MyAsyncHttp: 从零实现一个简单的异步http框架  

* 由于本项目之目的是研究异步编程的底层原理，故未使用python原生的asyncio以及其他第三方库，单纯使用socket+epoll实现
* 最初实现的版本只支持回调的代码结构。为避免层层回调（所谓“回调地狱”）带来的编码困难，开发了协程版本，支持yield from语法。
* 默认使用的是协程版本，如果要使用回调版本，则需要from MyAsyncHttp.callback_version import Server
* 在单线程异步框架中，必须处处异步，否则将阻塞线程。故在async_io_utils包中，简单实现了一个异步http请求库。后续将考虑加入异步文件IO的支持。


代码用例：
```python
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


from MyAsyncHttp import Server,Request
from MyAsyncHttp import async_io

server = Server('127.0.0.1', 8000)

@server.router.rule("/", method="GET")
def index(request: Request):
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
```
