# coding=utf-8
import queue
import select
import traceback
import logging
from socket import *
from . import container
from .http_utils import parse_http_request
from .loop import get_event_loop
from .request import Request
from .response import HttpResponse, HttpResponse404, HttpResponse500
from .router import Router


class Server(object):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.router = Router()
        self.loop = get_event_loop()

    def accept_callback(self, fd, event):
        '''
        有新的连接到来
        :param fd:
        :param event:
        :return:
        '''
        server_socket, event_type = container.get_fd_infos(fd)
        conn_socket, address = server_socket.accept()
        conn_socket.setblocking(False)
        container.add_fd_infos(conn_socket.fileno(), conn_socket, "socket")
        self.loop.register(conn_socket.fileno(), select.EPOLLIN, self.epollin_event_callback)
        #self.loop.register(conn_socket.fileno(), select.EPOLLHUP, self.epollhup_event_callback)

    def epollin_event_callback(self, fd, event):
        '''
        有socket数据读入,即收到了http客户端发来的数据
        :param fd:
        :param event:
        :return:
        '''

        event_socket, event_type = container.get_fd_infos(fd)
        recv_data = event_socket.recv(1024)
        if len(recv_data) == 0:
            print("连接断开")
            self.loop.unregister(fd)
            event_socket.close()
            container.del_fd_infos(fd)
        else:
            print("可读:")
            try:
                request = parse_http_request(recv_data.decode('ascii'))
                if self.check_request(request):
                    response = HttpResponse(fd)
                    self.router.get_handle(request.end_point, request.method)(request, response)
                else:
                    response_404 = HttpResponse404(fd)
                    response_404.write()
            except Exception as e:
                error_stack_msg = traceback.format_exc()
                print(e, error_stack_msg)
                logging.error(error_stack_msg)
                response_500 = HttpResponse500(fd)
                response_500.write(error_stack_msg)
            finally:
                self.loop.unregister(fd)
                self.loop.register(fd, select.EPOLLOUT, self.epollout_event_callback)


    def epollout_event_callback(self, fd, event):
        '''
        socket可写，此时可以向客户端发送http报文
        :param fd:
        :param event:
        :return:
        '''
        event_socket, event_type = container.get_fd_infos(fd)
        try:
            response_data = container.write_buffer[fd].get_nowait()
            event_socket.send(response_data)
        except queue.Empty as e:
            event_socket.close()
            self.loop.unregister(fd)
            container.del_fd_infos(fd)

    def epollhup_event_callback(self, fd, event):
        pass

    def check_request(self, request: Request):
        return self.router.has_end_point_method(request.end_point, request.method)

    def start(self):
        # 创建套接字
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        container.add_fd_infos(self.server_socket.fileno(), self.server_socket, "socket")
        # 设置当服务器先close 即服务器端4次挥手之后资源能够立即释放，这样就保证了，下次运行程序时 可以立即绑定端口
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(10)  # 最多可以监听10个连接
        self.server_socket.setblocking(False)  # 非阻塞
        self.loop.register(self.server_socket.fileno(), select.EPOLLIN, self.accept_callback)
        self.loop.start()