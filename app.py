from MyAsyncHttp import Server,Request,HttpResponse
import MyAsyncHttp.async_io_utils.async_http_request as async_http_request

server = Server('127.0.0.1', 8000)

@server.router.rule("/", method="GET")
def index(request: Request, response: HttpResponse):
    response.write("welcome to index")

@server.router.rule("/hello", method="GET")
def hello(request: Request, response: HttpResponse):
    name = request.params['name']
    response.write("hello," + name)

@server.router.rule("/baidu", method="GET")
def baidu(request: Request, response: HttpResponse):
    def success(data):
        response.write(data)

    def error(e, etb):
        response.set_status_code(500)
        response.write(etb)

    url = "http://www.baidu.com"
    async_http_request.request("GET", url, header=[],
                               success_callback=success, error_callback=error)


server.start()