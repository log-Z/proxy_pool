from threading import RLock, Thread
from database import MySQLOperation
from concurrent.futures import ThreadPoolExecutor


class HandlerContext:
    def __init__(self, job_name, job_time=None, logger=None): 
        self.job_name = job_name
        self.job_time = job_time
        self.logger = logger


class Handler:
    def __init__(self, context=None):
        self._context = context

    def handle(self, data):
        raise NotImplementedError()


class BufferHandler(Handler):
    def __init__(self, context=None):
        super().__init__(context)
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
    def __init__(self, buffer_size:int, concurrency:int, context=None):
        super().__init__(context)
        self._buffer_size = buffer_size
        self._lock = RLock()
        self._executor = ThreadPoolExecutor(concurrency)

    def handle(self, data):
        self._lock.acquire()
        if len(self._buffer) >= self._buffer_size:
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
        try:
            self._operator().batch_insert(self.clear())
        except:
            if self._context and self._context.logger:
                self._context.logger.exception(f'OnceInsertDatabase: Failed be insert data.')
            raise


class StreamInsertDatabase(StreamDatabaseOperation):
    def batch_handle(self, data_list:list):
        try:
            self._operator().batch_insert(data_list)
        except:
            if self._context and self._context.logger:
                self._context.logger.exception(f'StreamInsertDatabase: Failed be insert data.')
            raise


class MySQLOperationMixin(DatabaseOperationMixin):
    def _operator(self):
        return MySQLOperation
    

class MySQLOnceInserter(OnceInsertDatabase, MySQLOperationMixin):
    pass


class MySQLStreamInserter(StreamInsertDatabase, MySQLOperationMixin):
    pass


class ProxyValidateHandler(Handler):
    def __init__(self, proxy_handler=None, test_log_handler=None, proxy_test_filter=None, context=None):
        super().__init__(context)
        self.__proxy_handler = proxy_handler
        self.__test_log_handler = test_log_handler
        self.__proxy_test_filter = proxy_test_filter

    def handle(self, result:dict):
        proxy = result['proxy']
        test_logs = result['test_logs']
        if self._context and self._context.logger:
            self._context.logger.info(f'ProxyValidateHandler: Handling test result from proxy "{proxy.proxy_url}".')

        try:
            if self.__proxy_test_filter is None or self.__proxy_test_filter.assess(proxy, test_logs):
                if self.__proxy_handler is not None:
                    self.__proxy_handler.handle(proxy)
                if self.__test_log_handler is not None:
                    for tl in test_logs:
                        self.__test_log_handler.handle(tl)
        except:
            if self._context and self._context.logger:
                self._context.logger.exception(f'ProxyValidateHandler: Failed be handle test result from proxy "{proxy.proxy_url}".')
            raise

    def close(self):
        self.__proxy_handler.close()
        self.__test_log_handler.close()
