class Router(object):

    def __init__(self):
        self._rule_map = {
            "GET": {},
            "POST": {},
            "PUT": {},
            "DELETE": {}
        }

    def rule(self, url, method):
        def wrapper(fun):
            print(method, url, fun)
            self._rule_map[method][url] = fun
            return fun
        return wrapper

    def get_handle(self, end_point, method):
        return self._rule_map[method][end_point]

    def has_end_point_method(self, end_point, method):
        if self._rule_map.get(method) is None:
            return False
        elif self._rule_map.get(method).get(end_point) is None:
            return False
        return True
