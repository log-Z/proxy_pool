# 轻量IP代理池 PROXY POOL

> Pull 代码时请当心原有的 `config.py` 和 `jobs.py` 文件会被覆盖。

> 此项目尚为 `预览版` ，不能保证高可用性，各个模块仍会有大改动的可能性。

## 功能
1. 抓取网络上发布的免费IP代理。
1. 验证代理有效性。
1. 持久化代理到 MySQL 数据库中。


## 起步

### 运行环境
仅支持 Python 3.x 版本。

### 安装依赖
```shell
$ pip install -r requirements.txt
```

### 创建数据库
1. 建库语句位于 [`SQL/create_database.sql`](SQL/create_database.sql) 文件中，请手动创建数据库。
1. 建表语句位于 [`SQL/create_tables.sql`](SQL/create_tables.sql) 文件中，请手动创建所有的表。
> 为了避免插入顺序的限制，请不要设置任何外键约束！

### 修改全局配置
在 `config.py` 模块的 `Config` 类中修改配置信息，这是它本身的样子：
```python
class Config:

    # 必须。指定当前主机的位置信息。
    local = 'home'

    # 必须。指定数据库连接信息。
    database = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'db': 'proxy_pool',
        'charset': 'utf8mb4',
    }

    # 必须。指定日志信息。
    log = {
        # 可选。指定日志级别，有效值为 debug、info、warning、error、critical 之一。
        'level': 'info',
        # 可选。指定日志文件的绝对路径。
        'path': 'D:/temp/proxy_pool/job.log',
    }
```

### 添加作业
在 `jobs.py` 模块的 `Job` 类中添加作业方法，方法名称必须为 `job_作业名称` ，参数列表必须包含 `self` 和 `context` 这两个形参。下面是附带的例子：
```python
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
        num=50,                                 # 需要加载的代理数量
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
```

### 启动作业
假设，启动名称是 `001` 的单个作业：
```shell
$ python jobs.py start 001
```
假设，启动名称分别是 `001` 、 `002` 和 `003` 的多个作业，先后顺序等于启动顺序：
```shell
$ python jobs.py start 001 002 003
```


## 数据预览
### PROXY 表
|proxy_url|ip|port|protocol|local|collect_time|
|--|--|--:|--|--|--|
|http://95.101.178.172:8080|95.101.178.172|80|http|home|2020-07-25 10:41:31|
|http://95.179.233.141:8080|95.179.233.141|8080|http|home|2020-07-25 10:41:31|
|https://217.69.11.154:3128|217.69.11.154|3128|https|home|2020-07-25 10:41:31|
|https://78.141.134.204:8080|78.141.134.204|8080|https|home|2020-07-25 10:41:31|

### TEST_LOG 表
|id|proxy_url|website_name|website_url|response_elapsed|transfer_elapsed|transfer_size|timeout_exception|proxy_exception|test_time|job_time|verification_ip|response_head|response_body|exception|
|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
|1|http://95.101.178.172:8080|xxx|http://...|1.3532|1.3564|797|0|0|2020-07-25 11:14:05|2020-07-25 11:13:23|1|{ ... }|...|
|2|http://95.179.233.141:8080|xxx|http://...|4.5707|4.5748|797|0|0|2020-07-25 11:13:59|2020-07-25 11:13:23|1|{ ... }|...|
|3|https://217.69.11.154:3128|xxx|http://...|2.3773|2.3826|568|0|1|2020-07-19 17:31:51|2020-07-19 17:35:07|1|{ ... }|...|
|4|https://78.141.134.204:8080|xxx|http://...|0.0000|0.0000|0|0|0|2020-07-19 17:31:56|2020-07-19 17:35:07|1|||...|


## 文档
### 模块概览
* `iproxy.py` ：包含代理池、代理加载器、代理验证器等。
* `handler.py` ：包含代理处理器、测试日志处理器、验证处理器等。
* `database.py` ：数据库相关操作工具包。
* `models.py` ：持久层的实体模型。
* `config.py` : 全局配置。
* `jobs.py` ：作业管理，支持快速启动作业。
> 原来的 `proxy_pool.py` 已经废弃，将会择机删除！

### iproxy.py
代理池
* `ProxyPool` ：代理池。

代理加载器
* `ProxyLoader` ：代理加载器。
* `ProxySpider` ：代理爬虫，继承自 `ProxyLoader` 类。
* `XxxProxySpider` ：针对某个网站的代理爬虫，继承自 `ProxyLoader` 类。

代理验证器
* `ProxyValidator` ：代理验证器。
* `IPValidator` ：IP验证器，继承自 `ProxyValidator` 类。
* `KeywordValidator` ：关键词验证器，继承自 `ProxyValidator` 类。

上下文（Context）
* `ProxyPoolContext` ：代理池上下文。
* `ProxyLoaderContext` ：代理加载器上下文。
* `ProxyValidatorContext` ：代理验证器上下文。

### handler.py
处理器
* `Handler` ：处理器。
* `BufferHandler` ：缓冲处理器，继承自 `Handler` 类。
* `OnceHandler` ：一次性处理器，继承自 `BufferHandler` 类。
* `StreamHandler` ：流式处理器，继承自 `BufferHandler` 类。
* `OnceDatabaseOperation` ：一次性数据库操作处理器，继承自 `OnceHandler` 和 `DatabaseOperationMixin` 类。
* `StreamDatabaseOperation` ：流式数据库操作处理器，继承自 `StreamHandler` 和 `DatabaseOperationMixin` 类。
* `OnceInsertDatabase` ：一次性数据插入处理器，继承自 `OnceDatabaseOperation` 类。
* `StreamInsertDatabase` ：流式数据插入处理器，继承自 `StreamDatabaseOperation` 类。
* `MySQLOnceInserter` ：MySQL一次性数据插入处理器，继承自 `OnceInsertDatabase` 和 `MySQLOperationMixin` 类。
* `MySQLStreamInserter` ：MySQL流式数据插入处理器，继承自 `StreamInsertDatabase` 和 `MySQLOperationMixin` 类。
* `ProxyValidateHandler` ：代理验证处理器，继承自 `Handler` 类。

混入（Mixin）
* `DatabaseOperationMixin` ：数据库操作混入。
* `MySQLOperationMixin` ：MySQL数据库操作混入，继承自 `DatabaseOperationMixin` 类。

上下文（Context）
* `HandlerContext` ：处理器上下文。

### filter.py
* `ProxyFilter` ：代理过滤器。
* `SimpleProxyFilter` ：简单的代理过滤器，继承自 `ProxyFilter` 类。
* `ProxyTestFilter` ：代理测试过滤器。
* `SimpleProxyTestFilter` ：简单的代理测试过滤器，继承自 `ProxyTestFilter` 类。

### database.py
* `MySQLOperation` ：MySQL数据库操作工具包。

### models.py
字段
* `Field` ：字段。与数据表字段对应。
* `TextField` ：文本字段，继承自 `Field` 类。
* `NumberField` ：数值字段，继承自 `Field` 类。
* `BooleanField` ：布尔字段，继承自 `Field` 类。
* `DatetimeField` ：日期时间字段，继承自 `Field` 类。

模型
* `Model` ：模型。与数据表对应。

自定义模型
* `Proxy` ：代理表模型，继承自 `Model` 类。
* `TestLog` ：测试日志模型，继承自 `Model` 类。

### config.py
* `Config` ：全局配置。

### jobs.py
* `Job` ：作业管理。
* `JobContext` ：作业上下文。
