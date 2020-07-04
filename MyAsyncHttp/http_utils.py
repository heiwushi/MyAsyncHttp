from .request import Request


def parse_http_request(recv_data):
    """为一个客户端服务"""
    request_lines = recv_data.splitlines()
    method, url, http_version = request_lines[0].split(' ')
    if method == "GET":
        if "?" in url:
            end_point, url_params_part = url.split('?')
        else:
            end_point = url
            url_params_part = ""
    elif method == "POST":
        end_point = url

    headers = {}
    header_finish = False
    data = []
    params = {}
    for line in request_lines[1:]:
        print(line)
        if line != "":
            if header_finish:
                header_name, header_value = line.split(":")
                headers[header_name] = header_value
            else:
                data.append(line)
        else:
            header_finish = True
    # 下面解析参数
    method = method.upper()
    if method == "GET":
        if url_params_part != "":
            param_value_list = url_params_part.split('&')
            for param_value in param_value_list:
                param, value = param_value.split('=')
                params[param] = value
    return Request(end_point, method, http_version, headers, data, params)


def parse_http_response(recv_data):
    """为一个客户端服务"""
    request_lines = recv_data.splitlines()
    http_version, status_code, status_info = request_lines[0].split(' ')
    status_code = int(status_code)


    headers = {}
    header_finish = False
    data = []
    params = {}
    for line in request_lines[1:]:
        print(line)
        if line != "":
            if header_finish:
                header_name, header_value = line.split(" ")
                headers[header_name] = header_value
            else:
                data.append(line)
        else:
            header_finish = True
    return data
