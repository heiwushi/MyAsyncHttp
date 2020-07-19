from MyAsyncHttp.callback_version.loop import get_event_loop
import socket
from MyAsyncHttp.callback_version.fd_manger import FdManger
from MyAsyncHttp.callback_version.http_utils import parse_http_response_header
import select
from collections import defaultdict
import traceback as tb
import logging
loop = get_event_loop()

fd_manager = FdManger()

DEFAULT_HEADER = {
    "CONNECTION": "close", #暂时不支持keep-alive
}

HTTP_VERSION = "HTTP/1.1"


fd_callback_dict = defaultdict(dict)


def _epollin_event_callback(fd, event):
    '''
    有socket数据读入,即收到了访问的server发来的数据
    :param fd:
    :param event:
    :return:
    '''

    event_socket = fd_manager[fd].fd_file
    recv_data = event_socket.recv(1024)
    if len(recv_data) == 0:
        loop.unregister(fd)
        event_socket.close()
        fd_manager.del_fd(fd)
    else:
        try:
            fd_manager[fd].read_buffer += recv_data
            if not fd_manager[fd].have_read_header and b'\r\n\r\n' in fd_manager[fd].read_buffer:#说明响应头已经收到了,解析响应头
                head_finish_index = fd_manager[fd].read_buffer.index(b'\r\n\r\n')+4
                body_start_index = head_finish_index
                header_data = fd_manager[fd].read_buffer[0:head_finish_index]
                fd_manager[fd].read_buffer = fd_manager[fd].read_buffer[body_start_index:]#只保留请求体部分
                header = parse_http_response_header(header_data)
                if header.get("Content-Length"):
                    content_length = int(header.get("Content-Length"))
                    fd_manager[fd].read_content_length = content_length
                    fd_manager[fd].have_read_header = True
                else:
                    #暂时要求响应头必须包含content-length
                    raise Exception("content-length can't be empty")

            if fd_manager[fd].have_read_header and len(fd_manager[fd].read_buffer) == fd_manager[fd].read_content_length:
                body_data = fd_manager[fd].read_buffer
                fd_callback_dict[fd]["success"](body_data)
                loop.unregister(fd)
                fd_manager.del_fd(fd)
        except Exception as e:
            print(tb.format_exc())
            error_stack_msg = tb.format_exc()
            logging.error(error_stack_msg)
            loop.unregister(fd)
            fd_manager.del_fd(fd)

def _epollout_event_callback(fd, event):
    '''
    socket可写，此时可以向服务端发送http报文
    :param fd:
    :param event:
    :return:
    '''
    event_socket = fd_manager[fd].fd_file

    if len(fd_manager[fd].write_buffer)>0:
        event_socket.send(fd_manager[fd].write_buffer)
        loop.unregister(fd)
        loop.register(fd, select.EPOLLIN, _epollin_event_callback)


def build_http_header_line(method, endpoint, header):
    request_msg = ""
    request_msg += method + " " + endpoint + " " + HTTP_VERSION + "\r\n"
    for head_name in header:
        request_msg += head_name+":"+header[head_name]+"\r\n"
    request_msg += "\r\n"
    return request_msg


def request(method: str, url: str, header=None, success_callback=None, error_callback=None):
    try:
        assert url.startswith("http://")#暂时只支持http协议
        method = method.upper()
        url=url.replace("http://", "")
        url_splits = url.split('/')
        address_port = url_splits[0].split(":")
        if len(address_port) == 1:
            address = address_port[0]
            port = 80
        else:
            address, port = address_port

        if len(url_splits) > 1:
            end_point = "/" + "/".join(url_splits[1:])
        else:
            end_point = "/"
        header=dict(header)
        header.update(DEFAULT_HEADER)
        header["HOST"]=address
        request_msg = build_http_header_line(method, end_point, header)
        request_bytes = request_msg.encode('ascii')
        print(request_msg)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fd = client_socket.fileno()
        fd_callback_dict[fd]["success"] = success_callback
        fd_callback_dict[fd]["error"] = error_callback
        fd_manager.add_fd(fd, client_socket, "socket")
        fd_manager[fd].write_buffer+=request_bytes
        server_address = (address, port)
        client_socket.setblocking(False)
        try:
            client_socket.connect(server_address)
        except BlockingIOError as e:
            pass
        loop.register(fd, select.EPOLLOUT, _epollout_event_callback)
        loop.start()
    except Exception as e:
        error_callback(e, tb.format_exc())

