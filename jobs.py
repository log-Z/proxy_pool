import sys, logging
from datetime import datetime as Datetime
from config import Config
from iproxy import ProxyPool
from util import trim_margin, mkdir_if_notexists
from filter import SimpleProxyFilter, SimpleProxyTestFilter

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

        from iproxy import ProxyPoolContext, ProxyLoaderContext, ProxyValidatorContext, \
            FatezeroProxySpider, IPValidator
        from handler import HandlerContext, ProxyValidateHandler, MySQLStreamInserter
        from datetime import timedelta as Timedelta

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
        loader = FatezeroProxySpider(
            timeout=60,                             # 设置超时（可选）
            num=5000,                                 # 需要加载的代理数量
            context=ProxyLoaderContext(**ctx),
        )
        # 执行加载
        pool.load(loader)

        ## 3. 准备验证器
        v = IPValidator(
            **IPValidator.PLAN_IP138,               # 指定验证方式，这里使用预定义方案
            timeout=5,                              # 设置超时（可选）
            context=ProxyValidatorContext(**ctx),
        )

        ## 4. 准备过滤器
        # 创建代理过滤器（以下参数都是可选的）
        pf = SimpleProxyFilter(
            # port_list=[80, 8080],                 # 端口号
            # protocol_list=['http', 'https'],      # 协议
            # local_list=['home'],                  # 验证地区
            # collected_timedelta=Timedelta(days=1),# 收录时间与当前时间的距离（最大值）
        )
        # 创建代理测试过滤器（以下参数都是可选的）
        ptf = SimpleProxyTestFilter(
            proxy_filter=pf,                        # 代理过滤器
            response_elapsed_mean=6,                # 平均响应时长（最大值，秒）
            transfer_elapsed_mean=10,               # 平级传输时长（最大值，秒）
            timeout_exception_pr=0.34,              # 超时异常概率（最大值）
            proxy_exception_pr=0.34,                # 代理异常概率（最大值）
            valid_responses_pr=1,                   # 有效响应概率（最小值）
            pre_tested_timedelta=Timedelta(days=1), # 每个测试的前置条件-测试时间与当前时间的距离（最大值）
            pre_verification_ip=True,               # 每个测试的前置条件-是否经过IP验证
            # pre_valid_responses=True,             # 每个测试的前置条件-测是否有效响应
        )

        ## 5. 准备处理器
        # 创建代理处理器
        ph = MySQLStreamInserter(
            buffer_size=50,                         # 缓冲区大小
            concurrency=10,                         # 最大并发数量
            context=HandlerContext(**ctx),
        )
        # 创建测试日志处理器
        tlh = MySQLStreamInserter(
            buffer_size=50,                         # 缓冲区大小
            concurrency=10,                         # 最大并发数量
            context=HandlerContext(**ctx),
        )
        # 创建验证结果处理器，负责达标代理的处理（如入库）
        h = ProxyValidateHandler(
            proxy_handler=ph,                       # 针对Proxy的子处理器（可选）
            test_log_handler=tlh,                   # 针对TestLog的子处理器（可选）
            proxy_test_filter=ptf,                  # 指定过滤器，筛选达标的代理（可选）
            context=HandlerContext(**ctx),
        )
        
        ## 6. 执行验证
        pool.verify(
            validator=v,                            # 验证器
            handler=h,                              # 处理器
            repeat=3,                               # 每个代理的重复验证次数
            concurrency=10,                         # 最大并发数量
            sleep=1,                                # 线程间歇（秒）
        )


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
    if path:
        mkdir_if_notexists(path)
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
