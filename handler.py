from threading import RLock, Thread
from database import MySQLOperation
from concurrent.futures import ThreadPoolExecutor

class Handler:
    def handle(self, data):
        raise NotImplementedError()


class BufferHandler(Handler):
    def __init__(self):
        self._buffer = []
    
    def handle(self, data):
        self._buffer.append(data)

    def clear(self):
        old = self._buffer
        self._buffer = []
        return old


class OnceHandler(BufferHandler):
    def handle_all(self):
        raise NotImplementedError()


class StreamHandler(BufferHandler):
    def __init__(self, max_cache:int, concurrency:int):
        super().__init__()
        self._max_cache = max_cache
        self._lock = RLock()
        self._executor = ThreadPoolExecutor(concurrency)

    def handle(self, data):
        self._lock.acquire()
        if len(self._buffer) >= self._max_cache:
            self.flush()
        super().handle(data)
        self._lock.release()

    def flush(self):
        self._lock.acquire()
        old = self.clear()
        self._lock.release()
        self._executor.submit(self.__run, old)

    def close(self):
        self.flush()
        self._executor.shutdown(True)

    def batch_handle(self, data_list:list): 
        raise NotImplementedError()

    def __run(self, data_list:list):
        try:
            self.batch_handle(data_list)
        except Exception as e:
            half = len(data_list) // 2
            if half == 0:
                raise RuntimeError(str(data_list[0]), *e.args)
            self.__run(data_list[half:])
            self.__run(data_list[:half])


class DatabaseOperationMixin:
    def _operator(self):
        raise NotImplementedError()


class OnceDatabaseOperation(OnceHandler, DatabaseOperationMixin):
    pass


class StreamDatabaseOperation(StreamHandler, DatabaseOperationMixin):
    pass


class OnceInsertDatabase(OnceDatabaseOperation):
    def handle_all(self):
        self._operator().batch_insert(self.clear())


class StreamInsertDatabase(StreamDatabaseOperation):
    def batch_handle(self, data_list:list):
        self._operator().batch_insert(data_list)


class MySQLOperationMixin(DatabaseOperationMixin):
    def _operator(self):
        return MySQLOperation
    

class MySQLOnceInserter(OnceInsertDatabase, MySQLOperationMixin):
    pass


class MySQLStreamInserter(StreamInsertDatabase, MySQLOperationMixin):
    pass


class ProxyValidateHandler(Handler):
    def __init__(self, proxy_handler=None, test_log_handler=None):
        self.__proxy_handler = proxy_handler
        self.__test_log_handler = test_log_handler

    def handle(self, result:dict):
        proxy = result['proxy']
        test_logs = result['test_logs']

        if self._qualify(test_logs):
            if self.__proxy_handler is not None:
                self.__proxy_handler.handle(proxy)
            if self.__test_log_handler is not None:
                for tl in test_logs:
                    self.__test_log_handler.handle(tl)

    def close(self):
        self.__proxy_handler.close()
        self.__test_log_handler.close()

    def _qualify(self, test_logs:list) -> bool:
        failures = len(test_logs)
        for tl in test_logs:
            if not tl.timeout_exception and not tl.proxy_exception and tl.response_elapsed < 10 and tl.transfer_size > 0:
                failures -= 1
        return failures == 0
