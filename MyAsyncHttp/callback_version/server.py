# coding=utf-8
import queue
import select
import traceback
import logging
from socket import *
from . fd_manger import FdManger
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
        self.fd_manager = FdManger()
        self.loop = get_event_loop()

    def accept_callback(self, fd, event):
        '''
        有新的连接到来
        :param fd:
        :param event:
        :return:
        '''
        server_socket = self.fd_manager[fd].fd_file
        conn_socket, address = server_socket.accept()
        conn_socket.setblocking(False)
        self.fd_manager.add_fd(conn_socket.fileno(), conn_socket, FdManger.SOCKET)
        self.loop.register(conn_socket.fileno(), select.EPOLLIN, self.epollin_event_callback)

    def epollin_event_callback(self, fd, event):
        '''
        有socket数据读入,即收到了http客户端发来的数据
        :param fd:
        :param event:
        :return:
        '''
        conn_socket = self.fd_manager[fd].fd_file
        recv_data = conn_socket.recv(1024)
        if len(recv_data) == 0:
            self.loop.unregister(fd)
            conn_socket.close()
            self.fd_manager.del_fd(fd)
        else:
            try:
                request = parse_http_request(recv_data.decode('ascii'))
                if self.check_request(request):
                    response = HttpResponse(fd, self.fd_manager)
                    handler = self.router.get_handler(request.end_point, request.method)
                    handler(request, response)
                else:
                    response_404 = HttpResponse404(fd, self.fd_manager)
                    response_404.write()
            except Exception as e:
                error_stack_msg = traceback.format_exc()
                logging.error(e)
                logging.error(error_stack_msg)
                response_500 = HttpResponse500(fd, self.fd_manager)
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
        conn_socket = self.fd_manager[fd].fd_file
        if len(self.fd_manager[fd].write_buffer) > 0:
            while len(self.fd_manager[fd].write_buffer) > 0: #说明response已经写入write_buffer
                response_data = self.fd_manager[fd].write_buffer[0:1024]
                self.fd_manager[fd].write_buffer = self.fd_manager[fd].write_buffer[1024:]
                conn_socket.send(response_data)
            conn_socket.close()
            self.loop.unregister(fd)
            self.fd_manager.del_fd(fd)


    def epollhup_event_callback(self, fd, event):
        pass

    def check_request(self, request: Request):
        return self.router.has_end_point_method(request.end_point, request.method)

    def start(self):
        # 创建套接字
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.fd_manager.add_fd(self.server_socket.fileno(), self.server_socket, FdManger.SOCKET)
        # 设置当服务器先close 即服务器端4次挥手之后资源能够立即释放，这样就保证了，下次运行程序时 可以立即绑定端口
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(10)  # 最多可以监听10个连接
        self.server_socket.setblocking(False)  # 非阻塞
        #conn_socket, address = self.server_socket.accept()

        print("Start listening:", self.ip, self.port)
        self.loop.register(self.server_socket.fileno(), select.EPOLLIN, self.accept_callback)
        self.loop.start()

