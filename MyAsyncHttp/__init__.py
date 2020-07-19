_CALLBACK_VERSION = False

def use_callback_version():
    global _CALLBACK_VERSION
    _CALLBACK_VERSION = True

if _CALLBACK_VERSION:
    from MyAsyncHttp.callback_version.request import Request
    from MyAsyncHttp.callback_version.response import HttpResponse
    from MyAsyncHttp.callback_version.server import Server
