from .furture import Future

class Task:

    def __init__(self, coro):
        self.coro = coro    # 协程
        future = Future("first")
        future.add_done_callback(self._step)
        future.set_result(None)

    def _step(self, future:Future):
        try:
            next_future = self.coro.send(future.result)
        except StopIteration as exc:   # 说明协程已经执行完毕，为协程设置值
            print(exc)
            return
        next_future.add_done_callback(self._step)

