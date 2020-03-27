# 轻量IP代理池 PROXY POOL

## 功能
1. 抓取网络上发布的IP代理；
1. 验证代理有效性；
1. 持久化代理池到 `JSON` 或 `CSV` 文件中。

## 持久化
### JSON格式
```json
[{
  "type": "http",
  "host": "213.62.29.138",
  "port": "8080",
  "response_time_3": -1,
  "response_time_0": -1,
  "response_time_1": -2,
  "response_time_2": -2,
  "response_time_4": -2
}, {
  "type": "http",
  "host": "41.161.50.2",
  "port": "37741",
  "response_time_0": -2,
  "response_time_1": -2,
  "response_time_2": 4.889,
  "response_time_3": -2,
  "response_time_4": -2
}, {
  "type": "http",
  "host": "123.74.44.137",
  "port": "9999",
  "response_time_1": 0.776,
  "response_time_4": 0.639,
  "response_time_0": 2.781,
  "response_time_2": 3.038,
  "response_time_3": 3.04
}]
```

### CSV格式
```
,host,port,response_time_0,response_time_1,response_time_2,response_time_3,response_time_4,type
0,213.62.29.138,8080,-1,-1,-2,-2,-2,http
1,41.161.50.2,37741,-2,-2,4.889,-2,-2,http
2,123.74.44.137,9999,2.781,0.776,3.038,3.04,0.639,http
```

## 文档
### ProxyPool 代理池

### ProxyLoader 代理加载器

### ProxySpider 代理爬虫
继承自 `ProxyLoader` 类。

### ProxyValidator 代理验证器

### IPValidator IP验证器
继承自 `ProxyValidator` 类。

### KeywordValidator 关键词验证器
继承自 `ProxyValidator` 类。
