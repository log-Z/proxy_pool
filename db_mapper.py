import database, models

class MySQLMapper:
    @staticmethod
    def find_proxies(pf_cond, ptf_cond, field_names):
        def join(iter, as_str=False):
            ls = [f"'{val}'" for val in iter] if as_str \
                else [str(val) for val in iter]
            return ','.join(ls)

        sql = '\n'.join((
            f"select {join(field_names)}",
            f"from (",
            f"    select {','.join(['p.' + f for f in field_names])}",
            f"        -- test_log 聚合条件",
            f"        , avg(tl.response_elapsed) response_elapsed_mean" if ptf_cond.get('response_elapsed_mean') else "",
            f"        , avg(tl.transfer_elapsed) transfer_elapsed_mean" if ptf_cond.get('transfer_elapsed_mean') else "",
            f"        , avg(tl.timeout_exception) timeout_exception_pr" if ptf_cond.get('timeout_exception_pr') else "",
            f"        , avg(tl.proxy_exception) proxy_exception_pr" if ptf_cond.get('proxy_exception_pr') else "",
            f"        , avg(tl.transfer_size > 0) valid_responses_pr" if ptf_cond.get('valid_responses_pr') else "",
            f"    from proxy p",
            f"        left join test_log tl on p.proxy_url = tl.proxy_url" if ptf_cond else "",
            f"    where 1 = 1",
            f"        -- test_log 前置条件",
            f"        and tl.transfer_size > 0" if ptf_cond.get('pre_valid_responses') else "",
            f"        and tl.verification_ip" if ptf_cond.get('pre_verification_ip') else "",
            f"        and tl.test_time > date_sub(now(), interval {ptf_cond.get('pre_tested_timedelta').total_seconds()} second)" if ptf_cond.get('pre_tested_timedelta') else "",
            f"    group by p.proxy_url",
            f"    having 1=1",
            f"        -- proxy 条件",
            f"        and p.port in ({join(pf_cond.get('port_list'))})" if pf_cond.get('port_list') else "",
            f"        and p.protocol in ({join(pf_cond.get('protocol_list'), as_str=True)})" if pf_cond.get('protocol_list') else "",
            f"        and p.local in ({join(pf_cond.get('local_list'), as_str=True)})" if pf_cond.get('local_list') else "",
            f"        and p.collect_time > date_sub(now(), interval {pf_cond.get('collected_timedelta').total_seconds()} second)" if pf_cond.get('collected_timedelta') else "",
            f") p",
            f"where 1 = 1",
            f"    -- test_log 聚合条件",
            f"    and response_elapsed_mean < {ptf_cond.get('response_elapsed_mean')}" if ptf_cond.get('response_elapsed_mean') else "",
            f"    and transfer_elapsed_mean < {ptf_cond.get('transfer_elapsed_mean')}" if ptf_cond.get('transfer_elapsed_mean') else "",
            f"    and timeout_exception_pr < {ptf_cond.get('timeout_exception_pr')}" if ptf_cond.get('timeout_exception_pr') else "",
            f"    and proxy_exception_pr < {ptf_cond.get('proxy_exception_pr')}" if ptf_cond.get('proxy_exception_pr') else "",
            f"    and valid_responses_pr >= {ptf_cond.get('valid_responses_pr')}" if ptf_cond.get('valid_responses_pr') else "",
        ))

        return database.MySQLOperation.query(sql, _type=models.Proxy)
