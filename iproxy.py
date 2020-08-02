import time, re, json, traceback, math
import requests
from datetime import datetime as Datetime
from concurrent.futures import ThreadPoolExecutor
from models import Proxy, TestLog
from config import Config


class ProxyPoolContext:
    def __init__(self, job_name, job_time=None, logger=None): 
        self.job_name = job_name
        self.job_time = job_time
        self.logger = logger


class ProxyPool:
    def __init__(self, context:ProxyPoolContext=None):
        self._proxylist:dict = []
        self._context = context
    
    def load(self, loader, override=True):
        if override:
            self._proxylist.clear()
        ls = loader.load()
        self._proxylist.extend(ls)

    def verify(self, validator, handler, repeat=1, concurrency=10, sleep=1):
        proxy_count = len(self._proxylist)
        progress_count = 0
        def run(proxy):
            time.sleep(sleep)
            test_logs = list([validator.verify(proxy) for _ in range(repeat)])
            data = dict(proxy=proxy, test_logs=test_logs)
            handler.handle(data)
            return proxy

        excutor = ThreadPoolExecutor(max_workers=concurrency)
        for proxy in excutor.map(run, self._proxylist):
            progress_count += 1
            progress = round(progress_count / proxy_count * 100, 2)
            
            print(f'Verified [ {progress}% | {progress_count}/{proxy_count} ] {proxy.proxy_url}')
            if self._context and self._context.logger:
                self._context.logger.info(f'ProxyPool: Verified [ {progress}% | {progress_count}/{proxy_count} ] {proxy.proxy_url}.')

        handler.close()

    # def to_json(self, fp:str):
    #     with open(fp, mode="w") as json_file:
    #         json.dump(self._proxylist, json_file)
    
    # def to_csv(self, fp:str):
    #     pandas.DataFrame(self._proxylist).to_csv(fp, encoding='utf-8')

    def __len__(self):
        return len(self._proxylist)


class ProxyLoaderContext:
    def __init__(self, job_name, job_time=None, logger=None): 
        self.job_name = job_name
        self.job_time = job_time
        self.logger = logger


class ProxyLoader:
    def __init__(self, context:ProxyLoaderContext=None):
        self._proxylist:dict = []
        self._context = context
    
    def load(self) -> list:
        raise NotImplementedError()

    @staticmethod
    def proxy_url(ip, port, protocol='http'):
        return f'{protocol}://{ip}:{port}'


class ProxySpider(ProxyLoader):
    def __init__(self, sys_proxy=None, timeout=60, num=1000, context=None):
        super().__init__(context)
        self._sys_proxy = sys_proxy
        self._timeout = timeout
        self._num = num


class FatezeroProxySpider(ProxySpider):
    _POOL_URL = 'http://proxylist.fatezero.org/proxy.list'

    def load(self) -> list:
        ls = []

        if self._context and self._context.logger:
            self._context.logger.info('FatezeroProxySpider: loading proxy list.')
        try:
            res = requests.get(FatezeroProxySpider._POOL_URL, proxies=self._sys_proxy, timeout=self._timeout)
            for text in res.text.split('\n'):
                try:
                    p = json.loads(text, encoding='utf-8')
                    proxy = Proxy()
                    proxy.ip = p['host']
                    proxy.port = p['port']
                    proxy.protocol = p['type']
                    proxy.proxy_url = self.proxy_url(proxy.ip, proxy.port, proxy.protocol)
                    proxy.collect_time = Datetime.now()
                    proxy.local = Config.local
                    ls.append(proxy)
                except:
                    pass
            if self._num is None:
                return ls
            else:
                return ls[:self._num]
        except:
            if self._context and self._context.logger:
                self._context.logger.exception('FatezeroProxySpider: Failed be load proxy list.')
            raise


class SixSixIPProxySpider(ProxySpider):
    _POOL_URL = 'http://www.66ip.cn/mo.php?tqsl={}'
    
    def load(self) -> list:
        ls = []
        if self._num is None:
            return ls

        if self._context and self._context.logger:
            self._context.logger.info('SixSixIPProxySpider: loading proxy list.')

        url = SixSixIPProxySpider._POOL_URL.format(self._num)
        reg = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)(?=<br />)')
        try:
            res = requests.get(url, proxies=self._sys_proxy, timeout=self._timeout)
            for match in reg.finditer(res.text):
                try:
                    for protocol in ('http', 'https'):
                        proxy = Proxy()
                        proxy.ip = match.group(1)
                        proxy.port = match.group(2)
                        proxy.protocol = protocol
                        proxy.proxy_url = self.proxy_url(proxy.ip, proxy.port, proxy.protocol)
                        proxy.collect_time = Datetime.now()
                        proxy.local = Config.local
                        ls.append(proxy)
                except:
                    pass
            return ls
        except:
            if self._context and self._context.logger:
                self._context.logger.exception('SixSixIPProxySpider: Failed be load proxy list.')
            raise


class ProxyValidatorContext:
    def __init__(self, job_name, job_time=None, logger=None): 
        self.job_name = job_name
        self.job_time = job_time
        self.logger = logger


class ProxyValidator:
    __REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

    def __init__(self, website_name, http_url, https_url, timeout, context=None):
        self._request_config = dict(timeout=timeout, headers=self.__REQUEST_HEADERS)
        self._website_name = website_name
        self._http_url = http_url
        self._https_url = https_url
        self._job_time = Datetime.now() if not context or not context.job_time else context.job_time
        self._verification_ip = False
        self._context = context

    def verify(self, proxy:Proxy) -> TestLog:
        if self._context and self._context.logger:
            validator_name = self.__class__.__name__
            self._context.logger.info(f'{validator_name}: Verifying proxy "{proxy.proxy_url}".')

        tl = TestLog()
        tl.proxy_url = proxy.proxy_url
        tl.website_name = self._website_name
        tl.website_url = self._get_url(proxy.protocol)
        tl.response_elapsed = 0
        tl.transfer_elapsed = 0
        tl.transfer_size = 0
        tl.timeout_exception = False
        tl.proxy_exception = False
        tl.test_time = Datetime.now()
        tl.job_time = self._job_time
        tl.verification_ip = self._verification_ip
        tl.response_head = None
        tl.response_body = None
        tl.exception = None

        if tl.website_url is None:
            return None
        try:
            proxies = {proxy.protocol: proxy.proxy_url}
            start = time.time()
            response = requests.get(tl.website_url, proxies=proxies, **self._request_config)
            end = time.time()

            tl.response_elapsed = round(response.elapsed.total_seconds(), 4)
            tl.transfer_elapsed = round(end - start, 4)
            tl.transfer_size = len(response.content)
            tl.proxy_exception = self._proxy_exception(proxy, response)
            tl.response_head = str(response.headers)
            tl.response_body = response.text
        except requests.Timeout:
            tl.timeout_exception = True
        except:
            tl.exception = traceback.format_exc()
        return tl

    def _get_url(self, protocol:str):
        if protocol == 'http':
            return self._http_url
        elif protocol == "https":
            return self._https_url
        else:
            return None

    def _proxy_exception(self, proxy:Proxy, response:requests.Response):
        return False


class IPValidator(ProxyValidator):
    PLAN_IP138 = dict(website_name='ip138.com', http_url='http://202020.ip138.com/', https_url='https://202020.ip138.com/')
    PLAN_IPINFO_IO = dict(website_name='ipinfo.io', http_url='http://ipinfo.io/ip', https_url='https://ipinfo.io/ip')
    PLAN_IP_CN = dict(website_name='ip.cn', http_url=None, https_url='https://ip.cn/')
    PLAN_WHATISMYIP_AKAMAI_COM = dict(website_name='whatismyip.akamai.com', http_url='http://whatismyip.akamai.com/', https_url='https://whatismyip.akamai.com/')

    def __init__(self, website_name, http_url, https_url, timeout=5, context=None):
        super().__init__(website_name, http_url, https_url, timeout, context)
        self._verification_ip = True

    def _proxy_exception(self, proxy:Proxy, response:requests.Response):
        return proxy.ip not in response.text


class KeywordValidator(ProxyValidator):
    PLAN_BAIDU_SUG = dict(website_name='百度SUG', http_url=None, https_url='https://www.baidu.com/su', kw='window.baidu.sug')
    PLAN_ZHIHU_SIGNIN = dict(website_name='知乎登录', http_url=None, https_url='https://www.zhihu.com/signin', kw='有问题，上知乎')

    def __init__(self, website_name, http_url, https_url, kw, timeout=5, context=None):
        super().__init__(website_name, http_url, https_url, timeout, context)
        self._kw = kw

    def _proxy_exception(self, proxy:Proxy, response:requests.Response):
        return self._kw not in response.text
