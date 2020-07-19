class _FdInfo(object):

    def __init__(self, fd, fd_file, fd_type):
        self.fd = fd
        self.fd_type = fd_type
        self.fd_file = fd_file
        self.read_buffer = bytes()
        self.write_buffer = bytes()
        self.read_content_length = None
        self.have_read_header = False


class FdManger(object):
    SOCKET = 1
    FILEIO = 2

    def __init__(self):
        self._fd_info_dict = {}

    def __getitem__(self, item):
        return self._fd_info_dict[item]

    def add_fd(self, fd, fd_file, fd_type):
        self._fd_info_dict[fd] = _FdInfo(fd, fd_file, fd_type)

    def del_fd(self, fd):
        del self._fd_info_dict[fd]