from MyAsyncHttp import Server,Request,HttpResponse

server = Server('127.0.0.1', 8000)

@server.router.rule("/", method="GET")
def index(request: Request, response: HttpResponse):
    response.write("welcome to index")

@server.router.rule("/hello", method="GET")
def hello(request: Request, response: HttpResponse):
    name = request.params['name']
    response.write("hello," + name)

server.start()