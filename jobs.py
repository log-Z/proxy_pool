import sys
from iproxy import ProxyPool

class Jobs:
    def start(self, names):
        methods = {n: getattr(self, f'job_{n}', None) for n in names}
        if None in methods.values():
            missing = ', '.join([n for n, m in methods.items() if m is None])
            print(f'There are missing jobs: {missing}')
        else:        
            [m() for m in methods.values()]
                
    def job_001(self):
        """这个作业的名称是 001
        
        启动方式：$ python jobs.py start 001
        """

        from iproxy import FatezeroProxySpider, IPValidator
        from handler import ProxyValidateHandler, MySQLStreamInserter

        ## 1. 创建代理池
        pool = ProxyPool()

        ## 2. 加载代理
        # 创建代理加载器
        loader = FatezeroProxySpider(num=50)
        # 并执行加载
        pool.load(loader)

        ## 3. 验证代理
        # 创建验证器
        v = IPValidator(**IPValidator.PLAN_IP138)
        # 创建代理处理器
        ph = MySQLStreamInserter(max_cache=50, concurrency=10)
        # 创建测试日志处理器
        tlh = MySQLStreamInserter(max_cache=50, concurrency=10)
        # 创建验证处理器，负责验证通过后的处理
        h = ProxyValidateHandler(ph, tlh)
        # 执行验证
        pool.verify(v, h, repeat=3)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Example:')
        print('$ python jobs.py start name')
        print('$ python jobs.py start name1 name2 name3 ...')
    elif sys.argv[1] == 'start':
        Jobs().start(sys.argv[2:])
