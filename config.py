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

        'mincached': 3,
        'maxcached': 20,
        'maxshared': None,
        'maxconnections': None,
        'blocking': True,
        'maxusage': None,
        'reset': None,
        'setsession': [],
        'ping': 1,
    }

    # 必须。指定日志信息。
    log = {
        # 可选。指定日志级别，有效值为 debug、info、warning、error、critical 之一。
        'level': 'info',
        # 可选。指定日志文件的绝对路径。
        'path': 'D:/temp/proxy_pool/job.log',
    }
