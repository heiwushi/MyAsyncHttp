class Request(object):
    def __init__(self, end_point, method, http_version, headers, data, params):
        self.end_point = end_point
        self.method = method
        self.http_version = http_version
        self.headers = headers
        self.data = data
        self.params = params
