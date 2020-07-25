from MyAsyncHttp.coroutine_version.loop import get_event_loop
import socket
from MyAsyncHttp.coroutine_version.fd_manger import FdManger
from MyAsyncHttp.coroutine_version.http_utils import parse_http_response_header
import select
from MyAsyncHttp.coroutine_version.future import Future
from collections import defaultdict
import traceback as tb
import logging

loop = get_event_loop()

fd_manager = FdManger()

DEFAULT_HEADER = {
    "CONNECTION": "close",  # 暂时不支持keep-alive
}

HTTP_VERSION = "HTTP/1.1"

fd_callback_dict = defaultdict(dict)


def build_http_header_line(method, endpoint, header):
    request_msg = ""
    request_msg += method + " " + endpoint + " " + HTTP_VERSION + "\r\n"
    for head_name in header:
        request_msg += head_name + ":" + header[head_name] + "\r\n"
    request_msg += "\r\n"
    return request_msg


def parse_host_port(url):
    url = url.replace("http://", "")
    url_splits = url.split('/')
    host_port = url_splits[0].split(":")
    if len(host_port) == 1:
        host = host_port[0]
        port = 80
    else:
        host, port = host_port

    if len(url_splits) > 1:
        end_point = "/" + "/".join(url_splits[1:])
    else:
        end_point = "/"
    return host, port, end_point


def add_default_header(header, host):
    header = dict(header)
    header.update(DEFAULT_HEADER)
    header["HOST"] = host
    return header


def connect(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    fd = client_socket.fileno()
    fd_manager.add_fd(fd, client_socket, "socket")
    client_socket.setblocking(False)
    try:
        client_socket.connect((host, port))
    except BlockingIOError:
        pass
    future = Future("connect")

    def on_connected(fd, event):
        future.set_result(True)  # 6.set_result时会调用回调方法，而回调方法又会调用send促使代码从注释3处继续向下走, is_connected收到的值为True

    loop.register(fd, select.EPOLLOUT, on_connected)
    is_connected = yield from future  # 3.执行到此处, 将表示建立连接的future返回给Task._step方法里send调用处，之后代码让出控制权
    loop.unregister(fd)
    return client_socket


def recv(client_socket):
    fd = client_socket.fileno()
    i = 0
    header = {}
    read_buffer = b''
    is_header_read = False
    content_length = None
    while True:
        future = Future("recv" + str(i))
        def on_reachable(fd, event):
            chunked = client_socket.recv(1024)
            future.set_result(chunked)

        loop.register(fd, select.EPOLLIN, on_reachable)
        chunked = yield from future
        if chunked == b'':  # 连接关闭
            loop.unregister(fd)
            client_socket.close()
            fd_manager.del_fd(fd)
            raise Exception('Remote connection close.')

        loop.unregister(fd)
        read_buffer += chunked

        if not is_header_read and b'\r\n\r\n' in read_buffer:  # 说明响应头已经收到了,解析响应头
            head_finish_index = read_buffer.index(b'\r\n\r\n') + 4
            body_start_index = head_finish_index
            header_data = read_buffer[0:head_finish_index]
            read_buffer = read_buffer[body_start_index:]  # 只保留请求体部分
            header = parse_http_response_header(header_data)
            if header.get("Content-Length"):
                content_length = int(header.get("Content-Length"))
                is_header_read = True
            else:
                # 暂时要求响应头必须包含content-length
                raise Exception("content-length can't be empty")
        if is_header_read and len(read_buffer) == content_length:
            body_data = read_buffer
            fd_manager.del_fd(fd)
            return header, body_data


def request(method, url, header=None):
    assert url.startswith("http://")  # 暂时只支持http协议
    method = method.upper()
    host, port, end_point = parse_host_port(url)
    header = add_default_header(header, host)
    request_msg = build_http_header_line(method, end_point, header)
    request_bytes = request_msg.encode('ascii')
    client_socket = yield from connect(host, port)
    client_socket.send(request_bytes)
    res_header, res_body = yield from recv(client_socket)

    client_socket.close()
    return res_header, res_body


# if __name__ == '__main__':
#     from MyAsyncHttp.coroutine_version.task import Task
#     def call_fun():
#         res_header, res_body = yield from request("GET", "http://www.baidu.com", header=[])
#         print(res_header)
#         print(res_body)
#
#
#     Task(call_fun())
#     loop.start()