import requests
import json
import time
import itertools
import re

from concurrent.futures import ThreadPoolExecutor
from pandas import DataFrame


## 系统代理，为requests的proxies格式
# SYSTEM_PROXY = {'http' : 'localhost:1081'}


#%%
class ProxyPool:
    def __init__(self):
        self.proxylist:dict = []
    
    def load(self, loader, override=True):
        if override:
            self.proxylist.clear()
        ls = loader.proxylist()
        self.proxylist.extend(ls)

    def verify(self, validator, repeat=1, concurrency=3, sleep=1):
        proxy_count = len(self.proxylist) * repeat
        progress_count = 0
        def run(iproxy):
            proxy, i = iproxy
            time.sleep(sleep)
            rt = validator.response_time(proxy['host'], proxy['port'], proxy['type'])
            response_time_key = f'response_time_{i}'
            proxy[response_time_key] = rt
            return proxy

        excutor = ThreadPoolExecutor(max_workers=concurrency)
        iproxy_iter = itertools.product(self.proxylist, range(repeat))
        for proxy in excutor.map(run, iproxy_iter):
            progress_count += 1
            progress = round(progress_count / proxy_count * 100, 2)
            print(f"{progress}%", proxy)

    def to_json(self, fp:str):
        with open(fp, mode="w") as json_file:
            json.dump(self.proxylist, json_file)
    
    def to_csv(self, fp:str):
        DataFrame(self.proxylist).to_csv(fp, encoding='utf-8')

    def __len__(self):
        return len(self.proxylist)


class ProxyLoader:
    def proxylist(self) -> list:
        raise RuntimeError('Unsupported method.')


class ProxySpider(ProxyLoader):
    def __init__(self, sys_proxy=None):
        self.sys_proxy = sys_proxy


class FatezeroProxySpider(ProxySpider):
    _POOL_URL = 'http://proxylist.fatezero.org/proxy.list'

    def __init__(self, sys_proxy=None, timeout=30):
        super().__init__(sys_proxy)
        self.timeout = timeout

    def proxylist(self) -> list:
        ls = []
        res = requests.get(FatezeroProxySpider._POOL_URL, proxies=self.sys_proxy)
        for proxy in res.text.split('\n'):
            try:
                p = json.loads(proxy, encoding='utf-8')
                ls.append({
                    'type': p['type'],
                    'host': p['host'],
                    'port': p['port'],
                    })
            except:
                pass
        return ls


class SixSixIPProxySpider(ProxySpider):
    _POOL_URL = 'http://www.66ip.cn/mo.php?tqsl={}'

    def __init__(self, sys_proxy=None, timeout=30, num=100):
        super().__init__(sys_proxy)
        self.timeout = timeout
        self.num = num
    
    def proxylist(self) -> list:
        ls = []
        url = SixSixIPProxySpider._POOL_URL.format(self.num)
        res = requests.get(url, proxies=self.sys_proxy)
        reg = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)(?=<br />)')
        for match in reg.finditer(res.text):
            try:
                ls.append({
                    'type': 'http',
                    'host': match.group(1),
                    'port': match.group(2),
                })
            except:
                pass
        return ls


class ProxyValidator:
    def __init__(self, url, timeout):
        self.timeout = timeout
        self.url = url

    def response_time(self, host, port, proxytype):
        proxies = {proxytype: f'{host}:{port}'}
        try:
            start_time = time.time()
            response = requests.get(self.url, timeout=self.timeout, proxies=proxies)
            end_time = time.time()

            if self.verify(response, host, port, proxytype):
                return round(end_time - start_time, 3)
            else:
                return -1
        except:
            return -2

    def verify(self, response, host, port, proxytype):
        raise RuntimeError('Unsupported method.')


class IPValidator(ProxyValidator):
    URL_IPINFO_IO = 'http://ipinfo.io/ip'
    URL_IP_CN = 'https://ip.cn/'
    URL_WHATISMYIP_AKAMAI_COM = 'http://whatismyip.akamai.com/'

    def __init__(self, url, timeout=5):
        super().__init__(url, timeout)
    
    def verify(self, response, host, port, proxytype):
        return host in response.text


class KeywordValidator(ProxyValidator):
    PLAN_BAIDU_SUG = ('https://www.baidu.com/su', 'window.baidu.sug')
    PLAN_ZHIHU_SIGNIN = ('https://www.zhihu.com/signin', '有问题，上知乎')

    def __init__(self, url, kw, timeout=5):
        super().__init__(url, timeout)
        self.kw = kw

    def verify(self, response, host, port, proxytype):
        return self.kw in response.text


## 初始化代理池
# proxy_loader = FatezeroProxySpider()
proxy_loader = SixSixIPProxySpider(num=1000)
proxy_pool = ProxyPool()
proxy_pool.load(proxy_loader)
print('load:', len(proxy_pool))

## 检测代理可用性
# proxy_validator = IPValidator(IPValidator.URL_IP_CN)
# proxy_validator = IPValidator(IPValidator.URL_IPINFO_IO)
proxy_validator = IPValidator(IPValidator.URL_WHATISMYIP_AKAMAI_COM)
# proxy_validator = KeywordValidator(*KeywordValidator.PLAN_BAIDU_SUG)
# proxy_validator = KeywordValidator(*KeywordValidator.PLAN_ZHIHU_SIGNIN)
proxy_pool.verify(proxy_validator, repeat=5, concurrency=30)

#%%
## 保存代理池到JSON文件
save_time = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
json_path = f"D:/temp/proxy/valid_proxy_{save_time}.json"
proxy_pool.to_json(json_path)

## 保存代理池到CSV文件
csv_path = f"D:/temp/proxy/valid_proxy_{save_time}.csv"
proxy_pool.to_csv(csv_path)

# %%
