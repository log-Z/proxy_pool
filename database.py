from models import Model
from config import Config
import pymysql

class MySQLOperation:
    @staticmethod
    def insert(entity:Model) -> bool:
        table = MySQLOperation.table_name(entity)
        fields = MySQLOperation.fields_substament(entity)
        values = MySQLOperation.__values_substament(entity)

        row_num = MySQLOperation.execute(f'insert into {table}({fields}) \nvalues ({values});')
        return row_num > 0

    @staticmethod
    def batch_insert(entity_list:list) -> int:
        if not entity_list:
            return
        table = MySQLOperation.table_name(entity_list[0])
        fields = MySQLOperation.fields_substament(entity_list[0])
        values_list = [MySQLOperation.__values_substament(entity) for entity in entity_list]
        mult_values = '\n, '.join(map(lambda values: '({})'.format(values), values_list))
        
        return MySQLOperation.execute(f'insert into {table}({fields}) \nvalues {mult_values};')

    @staticmethod
    def select_all(_type:type) -> list:
        if not isinstance(_type, type) or not issubclass(_type, Model):
            raise TypeError('Parameter "_type" must be a Model subtype')

        entity = _type()
        table = MySQLOperation.table_name(entity)
        fields = MySQLOperation.fields_substament(entity)
        return MySQLOperation.query(f'select {fields} from {table};', _type)

    @staticmethod
    def execute(sql:str) -> int:
        row_num = 0
        connect = pymysql.connect(**Config.database)
        with connect.cursor() as cursor:
            row_num = cursor.execute(sql)
            connect.commit()
        connect.close()
        return row_num

    @staticmethod
    def query(sql:str, _type:type) -> list:
        if not isinstance(_type, type) or not issubclass(_type, Model):
            raise TypeError('Parameter "_type" must be a Model subtype')

        result = []
        fields = _type()._metadata.keys()
        connect = pymysql.connect(**Config.database)
        with connect.cursor() as cursor:
            cursor.execute(sql)
            data = cursor.fetchall()
            cols = {d[0]: i for i, d in enumerate(cursor.description) if d[0] in fields}
            
            if not data: data = tuple()
            for row in data:
                entity = _type()
                for col, i in cols.items():
                    setattr(entity, col, row[i])
                result.append(entity)

        connect.close()
        return result

    @staticmethod
    def table_name(entity:Model) -> str:
        ls = list(entity.__class__.__name__)
        ls[0] = ls[0].lower()
        iter = map(lambda letter: letter if letter.islower() else f'_{letter.lower()}', ls)
        return ''.join(iter)

    @staticmethod
    def fields_substament(entity:Model) -> str:
        return ', '.join(entity._metadata.keys())

    @staticmethod
    def __values_substament(entity:Model, field_names:list=None) -> str:
        metadata = entity._metadata
        if field_names is None:
            field_names = metadata.keys()
        field_values = [metadata[fn].to_sql(getattr(entity, fn)) for fn in field_names]
        return ', '.join(field_values)
