from models import Model
from config import Config
import pymysql

class MySQLOperation:
    @staticmethod
    def insert(entity:Model):
        table = MySQLOperation.__table_name(entity)
        fields = MySQLOperation.__fields_substament(entity)
        values = MySQLOperation.__values_substament(entity)

        MySQLOperation.__execute(f'insert into {table}({fields}) \nvalues ({values});')

    @staticmethod
    def batch_insert(entity_list:list):
        if entity_list is None or len(entity_list) == 0:
            return
        table = MySQLOperation.__table_name(entity_list[0])
        fields = MySQLOperation.__fields_substament(entity_list[0])
        values_list = [MySQLOperation.__values_substament(entity) for entity in entity_list]
        mult_values = '\n, '.join(map(lambda values: '({})'.format(values), values_list))
        
        MySQLOperation.__execute(f'insert into {table}({fields}) \nvalues {mult_values};')

    @staticmethod
    def __execute(sql:str):
        with pymysql.connect(**Config.database) as cursor:
            cursor.execute(sql)

    @staticmethod
    def __table_name(entity:Model) -> str:
        ls = list(entity.__class__.__name__)
        ls[0] = ls[0].lower()
        iter = map(lambda letter: letter if letter.islower() else f'_{letter.lower()}', ls)
        return ''.join(iter)
        
    
    @staticmethod
    def __fields_substament(entity:Model) -> str:
        return ', '.join(entity._metadata.keys())

    @staticmethod
    def __values_substament(entity:Model, field_names:list=None) -> str:
        metadata = entity._metadata
        if field_names is None:
            field_names = metadata.keys()
        field_values = [metadata[fn].to_sql(getattr(entity, fn)) for fn in field_names]
        return ', '.join(field_values)
