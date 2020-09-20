from datetime import (
    datetime as Datetime,
    timedelta as Timedelta
)


class ProxyFilter:
    def assess(self, proxy) -> bool:
        return True


class SimpleProxyFilter(ProxyFilter):
    _SUPPORTED_CONDITION = ('port_list', 'protocol_list', 'local_list', 'collected_timedelta')

    def __init__(self, *args, **keyword):
        self._conditions = {k: v for k, v in keyword.items() if k in self._SUPPORTED_CONDITION}

    def assess(self, proxy) -> bool:
        return self.assess_port(proxy.port) and \
            self.assess_protocol(proxy.protocol) and \
            self.assess_local(proxy.local) and \
            self.assess_collected_timedelta(proxy.collect_time)

    def assess_port(self, port: str) -> bool:
        port_list = self._conditions.get('port_list')
        if isinstance(port_list, (list, tuple)):
            return port in port_list
        return True

    def assess_protocol(self, protocol: str) -> bool:
        protocol_list = self._conditions.get('protocol_list')
        if isinstance(protocol_list, (list, tuple)):
            return protocol in protocol_list
        return True

    def assess_local(self, local: str) -> bool:
        local_list = self._conditions.get('local_list')
        if isinstance(local_list, (list, tuple)):
            return local in local_list
        return True

    def assess_collected_timedelta(self, collect_time) -> bool:
        timedelta = self._conditions.get('collected_timedelta')
        if isinstance(timedelta, Timedelta):
            return Datetime.now() - collect_time < timedelta
        return True


class ProxyTestFilter:
    def __init__(self, proxy_filter: ProxyFilter=None):
        self._proxy_filter = proxy_filter

    def assess(self, proxy, test_logs: list) -> bool:
        return True


class SimpleProxyTestFilter(ProxyTestFilter):
    _SUPPORTED_CONDITION = (
        'response_elapsed_mean', 'transfer_elapsed_mean',
        'timeout_exception_pr', 'proxy_exception_pr', 'valid_responses_pr',
        'pre_valid_responses', 'pre_tested_timedelta', 'pre_verification_ip'
    )

    def __init__(self, proxy_filter: ProxyFilter=None, *args, **keyword):
        super().__init__(proxy_filter)
        self._conditions = {k: v for k, v in keyword.items() if k in self._SUPPORTED_CONDITION}
    
    def assess(self, proxy, test_logs: list) -> bool:
        # 评估 proxy
        if self._proxy_filter and not self._proxy_filter.assess(proxy):
            return False

        # 仅保留符合前置条件的TestLog，排除干扰项
        test_logs = list(filter(
            lambda tl: self.__assess_pre_tested_timedelta(tl) and \
                self.__assess_pre_valid_responses(tl) and \
                self.__assess_pre_verification_ip(tl),
            test_logs
        ))
        if len(test_logs) == 0:
            return False

        # 评估 test_logs
        return self.assess_response_elapsed_mean(proxy, test_logs) and \
            self.assess_transfer_elapsed_mean(proxy, test_logs) and \
            self.assess_timeout_exception_pr(proxy, test_logs) and \
            self.assess_proxy_exception_pr(proxy, test_logs) and \
            self.assess_valid_responses_pr(proxy, test_logs)

    def assess_response_elapsed_mean(self, proxy, test_logs: list) -> bool:
        response_elapsed_mean = self._conditions.get('response_elapsed_mean')
        if isinstance(response_elapsed_mean, (int, float)):
            elapsed_sum = sum([tl.response_elapsed for tl in test_logs if tl.response_elapsed > 0])
            elapsed_mean = elapsed_sum / len(test_logs)
            return elapsed_mean <= response_elapsed_mean
        return True

    def assess_transfer_elapsed_mean(self, proxy, test_logs: list) -> bool:
        transfer_elapsed_mean = self._conditions.get('transfer_elapsed_mean')
        if isinstance(transfer_elapsed_mean, (int, float)):
            elapsed_sum = sum([tl.transfer_elapsed for tl in test_logs if tl.transfer_elapsed > 0])
            elapsed_mean = elapsed_sum / len(test_logs)
            return elapsed_mean <= transfer_elapsed_mean
        return True

    def assess_timeout_exception_pr(self, proxy, test_logs: list) -> bool:
        timeout_exception_pr = self._conditions.get('timeout_exception_pr')
        if isinstance(timeout_exception_pr, (int, float)):
            count = len([1 for tl in test_logs if tl.timeout_exception])
            pr = count / len(test_logs)
            return pr <= timeout_exception_pr
        return True

    def assess_proxy_exception_pr(self, proxy, test_logs: list) -> bool:
        proxy_exception_pr = self._conditions.get('proxy_exception_pr')
        if isinstance(proxy_exception_pr, (int, float)):
            count = len([1 for tl in test_logs if tl.proxy_exception])
            pr = count / len(test_logs)
            return pr <= proxy_exception_pr
        return True

    def assess_valid_responses_pr(self, proxy, test_logs: list) -> bool:
        valid_responses_pr = self._conditions.get('valid_responses_pr')
        if isinstance(valid_responses_pr, (int, float)):
            count = len([1 for tl in test_logs if tl.transfer_size > 0])
            pr = count / len(test_logs)
            return pr >= valid_responses_pr
        return True

    def __assess_pre_valid_responses(self, tl) -> bool:
        valid_responses = self._conditions.get('pre_valid_responses')
        if valid_responses == True:
            return tl.transfer_size > 0
        return True

    def __assess_pre_tested_timedelta(self, tl) -> bool:
        timedelta = self._conditions.get('pre_tested_timedelta')
        if isinstance(timedelta, Timedelta):
            return Datetime.now() - tl.test_time < timedelta
        return True

    def __assess_pre_verification_ip(self, tl) -> bool:
        verification_ip = self._conditions.get('pre_verification_ip')
        if verification_ip == True:
            return tl.verification_ip
        return True
