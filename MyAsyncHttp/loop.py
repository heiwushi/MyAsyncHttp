import select
import logging
import traceback

class Loop(object):
    def __init__(self):
        self.epoll = select.epoll()
        self.fd_event_callback_dict = dict()

    def unregister(self, fd):
        self.epoll.unregister(fd)
        if self.fd_event_callback_dict.get(str(fd) + str(select.EPOLLHUP)):
            del self.fd_event_callback_dict[str(fd) + str(select.EPOLLHUP)]
        if self.fd_event_callback_dict.get(str(fd) + str(select.EPOLLIN)):
            del self.fd_event_callback_dict[str(fd) + str(select.EPOLLIN)]
        if self.fd_event_callback_dict.get(str(fd) + str(select.EPOLLOUT)):
            del self.fd_event_callback_dict[str(fd) + str(select.EPOLLOUT)]

    def register(self, fd, event_type, callback):
        self.epoll.register(fd, event_type)
        self.fd_event_callback_dict[str(fd) + str(event_type)] = callback


    def start(self):
        while True:
            events = self.epoll.poll(timeout=-1)
            for fd, event in events:
                callback = self.fd_event_callback_dict[str(fd) + str(event)]
                callback(fd, event)


_loop = Loop()


def get_event_loop():
    return _loop
