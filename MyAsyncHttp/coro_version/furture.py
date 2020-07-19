class Future:
    def __init__(self, name):
        self.name = name
        self.result = None
        self._callbacks = []

    def __str__(self):
        return self.name

    def add_done_callback(self, fn):#决定了运行结果出来set_result后要做什么
        self._callbacks.append(fn)

    def set_result(self, result):
        #当事件循环触发io完成的消息， 计算出结果后，调用该方法，设置Future的结果
        #设置的结果用途发给yield的接收处以继续循环
        self.result = result
        for fn in self._callbacks:
            fn(self)