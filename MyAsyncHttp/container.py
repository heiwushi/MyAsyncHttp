from collections import defaultdict
import queue

fd_infos = {}
write_buffer = defaultdict(queue.Queue)
read_buffer = defaultdict(bytes)
read_length_dict = {}


def add_fd_infos(fd, obj, obj_type):
    fd_infos[fd] = {
        "obj": obj,
        "obj_type": obj_type
    }

def get_fd_infos(fd):
    return fd_infos[fd]["obj"], fd_infos[fd]["obj_type"]


def del_fd_infos(fd):
    del fd_infos[fd]