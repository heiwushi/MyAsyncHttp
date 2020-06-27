from MyAsyncHttp.container import write_buffer
import json


class HttpResponse(object):

    DEFAULT_STATUS_CODE = 200

    def __init__(self,  fd):
        # 设置返回的头信息 header
        self._fd = fd
        self.headers = {}
        self.status_code = HttpResponse.DEFAULT_STATUS_CODE

    def set_status_code(self, status_code):
        self.status_code = status_code

    def set_headers(self, headers):
        self.headers.update(headers)

    def write(self, data=None):
        '''
        向write_buffer中写入响应body, 目前只支持写入
        :param data:
        :return:
        '''
        if self.status_code == 200:
            status_line = "HTTP/1.1 200 OK\r\n"
        elif self.status_code == 404:
            status_line = "HTTP/1.1 404 Not Found\r\n"
        elif self.status_code == 500:
            status_line = "HTTP/1.1 500 Internal Server Error\r\n"
        else:
            raise Exception("error status")
        res = status_line
        res += "\r\n"
        for header_name, header_value in self.headers:
            res += (header_name+":"+header_value+"\r\n")
        if data:
            res += "\r\n"
            if isinstance(data, dict):
                res+=json.dumps(data)
            elif isinstance(data, int):
                res+=str(int)
            elif isinstance(data, str):
                res+=data
        res_bytes = res.encode('ascii')
        write_buffer[self._fd].put_nowait(res_bytes)


class HttpResponse404(HttpResponse):
    def __init__(self, fd):
        super().__init__(fd)
        super().set_status_code(404)


class HttpResponse500(HttpResponse):
    def __init__(self, fd):
        super().__init__(fd)
        super().set_status_code(500)
