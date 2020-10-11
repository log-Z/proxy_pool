import time
from decimal import Decimal
from datetime import datetime as Datetime

class Field:
    def __init__(self, primary_key=False):
        self._is_primary_key = primary_key

    def to_sql(self, value):
        raise NotImplementedError()


class TextField(Field):
    def to_sql(self, value:str):
        if isinstance(value, str):
            return "'" + value.replace("'", "\\'") + "'"
        elif value is None:
            return 'null'
        raise RuntimeError(f'TextField value cannot be of type "{type(value)}", value is "{value}".')

    # TODO: 新增方法：有效值检查


class NumberField(Field):
    __SUPPORT_TYPE = (int, float, Decimal)

    def to_sql(self, value):
        if isinstance(value, self.__SUPPORT_TYPE):
            return str(value)
        elif isinstance(value, str) and self.__canConvert(value):
            return value
        elif value is None:
            return 'null'
        raise RuntimeError(f'NumberField value cannot be of type "{type(value)}", value is "{value}".')

    def __canConvert(self, value):
        for t in self.__SUPPORT_TYPE:
            try:
                t(value)
                return True
            except:
                continue
        return False


class BooleanField(Field):
    def to_sql(self, value):
        if isinstance(value, bool):
            return str(value)
        elif value is None:
            return 'null'
        raise RuntimeError(f'BooleanField value cannot be of type "{type(value)}", value is "{value}".')


class DatetimeField(Field):
    def to_sql(self, value):
        if isinstance(value, Datetime):
            return value.strftime('\'%Y-%m-%d %H:%M:%S\'')
        elif value is None:
            return 'null'
        raise RuntimeError(f'DatetimeField value cannot be of type "{type(value)}", value is "{value}".')


class Model:
    def __init__(self):
        self._metadata = {}
        for attr in vars(self.__class__).keys():
            if not attr.startswith('_') and not attr.endswith('_'):
                self._metadata[attr] = getattr(self.__class__, attr)
                setattr(self, attr, None)
    
    def __str__(self):
        fields = [f'{field}={getattr(self, field)}' for field in self._metadata.keys()]
        fields_str = ', '.join(fields)
        return f'{self.__class__.__name__}{{{fields_str}}}'


class Proxy(Model):
    proxy_url = TextField(primary_key=True)
    ip = TextField()
    port = NumberField()
    protocol = TextField()
    local = TextField()
    collect_time = DatetimeField()


class TestLog(Model):
    id = NumberField(primary_key=True)
    proxy_url = TextField()
    website_name = TextField()
    website_url = TextField()
    response_elapsed = NumberField()
    transfer_elapsed = NumberField()
    transfer_size = NumberField()
    timeout_exception = BooleanField()
    proxy_exception = BooleanField()
    test_time = DatetimeField()
    job_time = DatetimeField()
    verification_ip = BooleanField()
    response_head = TextField()
    response_body = TextField()
    exception = TextField()
