from .future import Future
import logging

class Task:
    def __init__(self, coro):
        self.coro = coro    # 协程
        self._step()  # 1.任务启动时先激活一下协程coro

    def _step(self, future: Future = None):
        try:
            if future:
                next_future = self.coro.send(future.result)  # 7. 当协程coro调用future.set_result时_，会向协程发送send回future的结果(发送给yield的接收方), 协程在中断处继续执行
            else:
                # 2. 只有第一次调用才会执行此处，激活协程coro
                next_future = self.coro.send(None)
                # 4. 收到第一个future
        except StopIteration as exc:
            print(future)
            print(exc)
            return
        next_future.add_done_callback(self._step)  #  5.为该future增加回调，而回调是_step方法自身，当协程coro调用future.set_result时_，会向协程发送send回future的结果
        #  执行后，在next_future.set_result之前（也就是异步IO完成之前，coro和Task均没有代码需要执行，控制权让给loop循环）

