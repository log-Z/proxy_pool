import sys, logging
from datetime import datetime as Datetime
from config import Config
from iproxy import ProxyPool
from util import trim_margin

class Jobs:
    def start(self, names):
        methods = {n: getattr(self, f'job_{n}', None) for n in names}
        if None in methods.values():
            missing = ', '.join([n for n, m in methods.items() if m is None])
            print(f'There are missing jobs: {missing}')
            return

        for n, m in methods.items():
            context = JobContext(n)
            try:
                m(context=context)
            except:
                context.logger.exception('An error occurred while running this job.')
                raise
                
    def job_001(self, context):
        """这个作业的名称是 001
        
        启动方式：$ python jobs.py start 001
        """

        from iproxy import ProxyPoolContext, ProxyLoaderContext, ProxyValidatorContext, FatezeroProxySpider, IPValidator
        from handler import HandlerContext, ProxyValidateHandler, MySQLStreamInserter

        ## 0. 配置上下文，为各个组件提供全局环境
        ctx = {
            'job_name': context.job_name,
            'job_time': context.job_time,
            'logger': context.logger,
        }

        ## 1. 创建代理池
        pool = ProxyPool(context=ProxyPoolContext(**ctx))

        ## 2. 加载代理
        # 创建代理加载器
        loader = FatezeroProxySpider(num=50, context=ProxyLoaderContext(**ctx))
        # 执行加载
        pool.load(loader)

        ## 3. 验证代理
        # 创建验证器
        v = IPValidator(**IPValidator.PLAN_IP138, context=ProxyValidatorContext(**ctx))
        # 创建代理处理器
        ph = MySQLStreamInserter(max_cache=50, concurrency=10, context=HandlerContext(**ctx))
        # 创建测试日志处理器
        tlh = MySQLStreamInserter(max_cache=50, concurrency=10, context=HandlerContext(**ctx))
        # 创建验证处理器，负责验证通过后的处理
        h = ProxyValidateHandler(proxy_handler=ph, test_log_handler=tlh, context=HandlerContext(**ctx))
        # 执行验证
        pool.verify(v, h, repeat=3)


class JobContext:
    def __init__(self, job_name): 
        self.job_name = job_name
        self.job_time = Datetime.now()

        logger_name = f"{self.job_name}_{self.job_time.strftime('%Y%m%d%H%M%S')}"
        self.logger = logging.getLogger(logger_name)


def init_logging():
    config = {
        'format': '> %(asctime)s | %(name)s | %(levelname)s | %(message)s',
    }

    path = Config.log.get('path')
    if path is not None:
        config['filename'] = path

    level = Config.log.get('level')
    if level == 'debug':
        config['level'] = logging.DEBUG
    elif level == 'info':
        config['level'] = logging.INFO
    elif level == 'warning':
        config['level'] = logging.WARNING
    elif level == 'error':
        config['level'] = logging.ERROR
    elif level == 'critical':
        config['level'] = logging.CRITICAL

    logging.basicConfig(**config)


if __name__ == '__main__':
    init_logging()

    if len(sys.argv) < 3:
        print(trim_margin('''
        |Example:
        |  $ python jobs.py start name
        |  $ python jobs.py start name1 name2 name3 ...
        '''))
    elif sys.argv[1] == 'start':
        Jobs().start(sys.argv[2:])
