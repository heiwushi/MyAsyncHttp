from ..loop import get_event_loop
import socket
from .. import container
from .. http_utils import parse_http_header
import select
import queue
from collections import defaultdict
import traceback as tb
import logging
loop = get_event_loop()


DEFAULT_HEADER = {
    "CONNECTION": "close", #暂时不支持keep-alive
}

HTTP_VERSION = "HTTP/1.1"


fd_callback_dict = defaultdict(dict)


def _epollin_event_callback(fd, event):
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
        loop.unregister(fd)
        event_socket.close()
        container.del_fd_infos(fd)
    else:
        print("可读:")
        try:
            recv_str = recv_data
            container.read_buffer[fd]+=recv_data
            if b'\r\n\r\n' in container.read_buffer[fd]:#说明响应头已经收到了,解析响应头
                head_finish_index = container.read_buffer[fd].index(b'\r\n\r\n')+4
                body_start_index = head_finish_index
                header = parse_http_header(container.read_buffer[fd][0:head_finish_index])
                if header.get("Content-Length"):
                    content_length = header.get("Content-Length")
            body_data = container.read_buffer[fd][body_start_index:]
            print(len(body_data))
            if len(body_data) == int(content_length):
                fd_callback_dict[fd]["success"](body_data)
                loop.unregister(fd)
                container.del_fd_infos(fd)




            #fd_callback_dict[fd]["success"](recv_data)
            #response = parse_http_response(recv_data.decode('utf-8'))

            #print(response)
        except Exception as e:
            print(tb.format_exc())
            error_stack_msg = tb.format_exc()
            logging.error(error_stack_msg)
            loop.unregister(fd)
            container.del_fd_infos(fd)

def _epollout_event_callback(fd, event):
    '''
    socket可写，此时可以向服务端发送http报文
    :param fd:
    :param event:
    :return:
    '''
    event_socket, event_type = container.get_fd_infos(fd)
    try:
        request_data = container.write_buffer[fd].get_nowait()
        event_socket.send(request_data)
        loop.unregister(fd)
        loop.register(fd, select.EPOLLIN, _epollin_event_callback)

    except queue.Empty as e:
        event_socket.close()
        loop.unregister(fd)
        container.del_fd_infos(fd)


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
        container.add_fd_infos(fd, client_socket, "socket")
        container.write_buffer[fd].put_nowait(request_bytes)
        server_address = (address, port)
        client_socket.connect(server_address)
        client_socket.setblocking(False)
        loop.register(fd, select.EPOLLOUT, _epollout_event_callback)
        loop.start()
    except Exception as e:
        error_callback(e, tb.format_exc())

