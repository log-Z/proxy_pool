-- 代理表
create table proxy (
  proxy_url varchar(40) primary key comment '代理URL',
  ip varchar(16) comment '代理IP',
  port int comment '代理端口',
  protocol char(5) comment '代理协议',
  local varchar(100) comment '当前位置',
  collect_time datetime comment '入池时间'
);

-- 测试表
create table test_log (
  id int(11) NOT NULL AUTO_INCREMENT primary key comment '代理ID',
  proxy_url varchar(40) comment '代理URL',
  website_name varchar(20) comment '测试网站名称',
  website_url varchar(100) comment '测试网站URL',
  response_elapsed decimal(8, 4) comment '响应时长',
  transfer_elapsed decimal(8, 4) comment '传输时长',
  transfer_size int comment '传输大小',
  timeout_exception boolean comment '是否超时',
  proxy_exception boolean comment '代理异常',
  test_time datetime comment '测试时间',
  job_time datetime comment '调度时间',
  verification_ip boolean comment '是否验证了IP',
  response_head text comment '响应头',
  response_body text comment '响应体',
  exception text comment '异常信息'
);
