from ..loop import get_event_loop
import socket
from .. import container
import select
import queue

loop = get_event_loop()


def _epollin_event_callback(fd, event):
    '''
    有socket数据读入,即收到了http服务端发来的数据
    :param fd:
    :param event:
    :return:
    '''
    pass


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
    except queue.Empty as e:
        event_socket.close()
        loop.unregister(fd)
        container.del_fd_infos(fd)


def get( url, success_callback, error_callback):
    url=url.replace("http://", "")
    address_port = url.split('/')[0].split(":")
    if len(address_port)==1:
        address = address_port
        port = 80
    else:
        address, port = address_port

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setblocking(False)
    container.write_buffer[client_socket.fileno()].put_nowait("")
    container.add_fd_infos(client_socket.fileno(), client_socket, "socket")
    server_address = (address, port)
    client_socket.connect(server_address)
    loop.register(client_socket.fileno(), select.EPOLLOUT, _epollout_event_callback)
