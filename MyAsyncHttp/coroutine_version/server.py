# coding=utf-8
import select
import logging
import traceback
from inspect import isgeneratorfunction
from socket import *

from .fd_manger import FdManger
from .furture import Future
from .http_utils import parse_http_request
from .loop import get_event_loop
from .request import Request
from .response import HttpResponse, HttpResponse404
from .router import Router
from .task import Task

class Server(object):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.router = Router()
        self.fd_manager = FdManger()
        self.loop = get_event_loop()

    def start(self):
        Task(self.start_listen())
        self.loop.start()

    def start_listen(self):
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.fd_manager.add_fd(self.server_socket.fileno(), self.server_socket, FdManger.SOCKET)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(10)  # 最多可以监听10个连接
        self.server_socket.setblocking(False)  # 非阻塞
        while True:
            print("aaa")
            conn_socket = yield from self.accept(self.server_socket)
            Task(self.handler_conn_socket(conn_socket))



    def accept(self, server_socket):
        fd = self.server_socket.fileno()
        future = Future("connection_reachable")

        def connection_reachable(fd, event):
            conn_socket, address = server_socket.accept()
            conn_socket.setblocking(False)
            future.set_result(conn_socket)

        self.loop.register(fd, select.EPOLLIN, connection_reachable)
        conn_socket = yield future
        self.loop.unregister(fd)
        conn_socket.setblocking(False)
        return conn_socket

    def handler_conn_socket(self, conn_socket):

        fd = conn_socket.fileno()
        self.fd_manager.add_fd(fd, conn_socket, FdManger.SOCKET)
        try:
            request = yield from self.recv_request(conn_socket)
            print(request.end_point)
            response = yield from self.build_response(request)
            yield from self.send_response(conn_socket, response)
        except Exception as e:
            logging.error(e)
            logging.error(traceback.format_exc())
        finally:
            conn_socket.close()
            self.fd_manager.del_fd(fd)




    def check_request(self, request: Request):
        return self.router.has_end_point_method(request.end_point, request.method)

    def recv_request(self, conn_socket):
        fd = conn_socket.fileno()
        future = Future("request_reachable")

        def request_reachable(fd, event):
            recv_data = conn_socket.recv(1024)
            future.set_result(recv_data)

        self.loop.register(fd, select.EPOLLIN, request_reachable)

        recv_data = yield future

        self.loop.unregister(fd)

        if len(recv_data) == 0:
            conn_socket.close()
            raise Exception("recv 0 bytes request data")
        else:
            request = parse_http_request(recv_data.decode('ascii'))
        return request

    def send_response(self, conn_socket, response):
        fd = conn_socket.fileno()
        future = Future("writeable")

        def response_writeable(fd, event):
            future.set_result(True)

        self.loop.register(fd, select.EPOLLOUT, response_writeable)

        writeable = yield future

        self.loop.unregister(fd)
        write_buffer = response.get_write_buffer()
        while len(write_buffer) > 0:  # 说明response已经写入write_buffer
            response_data = write_buffer[0:1024]
            write_buffer = write_buffer[1024:]
            conn_socket.send(response_data)

    def build_response(self, request):
        if self.check_request(request):
            handler = self.router.get_handler(request.end_point, request.method)
            if isgeneratorfunction(handler):  # 判断是普通函数，还是带有yield from的生成器函数
                response_data = yield from handler(request)
            else:
                response_data = handler(request)
            response = HttpResponse()
            response.write(response_data)
        else:
            response = HttpResponse404()
            response.write()
        return response
