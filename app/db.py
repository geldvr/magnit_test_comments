import logging

import psycopg2

import config
from app import errors


class PostgresDB(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)

            conf = config.load_config(config.get_config_path(), {'postgres.port': 5432})

            postgres_config = {
                'host': conf['postgres.host'],
                'port': conf['postgres.port'],
                'dbname': conf['postgres.database'],
                'user': conf['postgres.user'],
                'password': conf['postgres.password']
            }

            try:
                logging.info('Connecting to postgres database...')
                connection = PostgresDB._instance.connection = psycopg2.connect(**postgres_config)
                cursor = PostgresDB._instance.cursor = connection.cursor()
                cursor.execute('select version()')
                db_version = cursor.fetchone()

            except Exception as conn_err:
                logging.exception('connection problem: %s', conn_err)
                PostgresDB._instance = None

            else:
                logging.info('connection established\n%s', db_version[0])

        return cls._instance

    def __init__(self):
        self.connection = self._instance.connection
        self.cursor = self._instance.cursor

    def __del__(self):
        self.connection.close()
        self.cursor.close()

    def query(self, query):
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as query_err:
            logging.error('query error : %s', query_err)
            raise errors.DatabaseException('db error on query data')

    def insert(self, query):
        return self._insert_or_delete(query)

    def delete(self, query):
        return self._insert_or_delete(query, 'delete')

    def _insert_or_delete(self, query, operation='insert'):
        try:
            self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as db_err:
            logging.error('{} error : %s'.format(operation), db_err)
            raise errors.DatabaseException('db error on {} data'.format(operation))
