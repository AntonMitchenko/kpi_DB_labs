import csv
import os
import time
import warnings
import logging

import psycopg2
import pandas as pd

from psycopg2 import OperationalError, sql


GENERAL_TABLE_NAME = "res_zno"
# DB_CONFIG = {'user': 'postgres',
#              'password': 'AI3006',
#              'host': 'localhost',
#              'port': 5432,
#              'database': 'zno'}
DB_CONFIG = {'user': os.getenv("DB_USER"),
             'password': os.getenv("DB_PASSWORD"),
             'host': os.getenv("DB_HOST"),
             'port': os.getenv("DB_PORT"),
             'database': os.getenv("DB_NAME")}

CSV_CONFIG = {
    'PATH_CONFIG': {
        2020: {'path': './data/Odata2020File.csv',
               'encoding': 'windows-1251'
               },
        2019: {'path': './data/Odata2019File.csv',
               'encoding': 'windows-1251'
               }
    },
    'OPEN_CONFIG': {
        'delimiter': ';'
    }
}


SQL_PARAM = {
    'QUERY': {
        'CREATE_TABLE': f"""
        CREATE TABLE {GENERAL_TABLE_NAME} (
        ID INTEGER,
        OUTID VARCHAR(255) PRIMARY KEY,
        Birth INTEGER,
        SEXTYPENAME VARCHAR(255),
        REGNAME VARCHAR(255),
        AREANAME VARCHAR(255),
        TERNAME VARCHAR(255),
        REGTYPENAME VARCHAR(255),
        TerTypeName VARCHAR(255),
        ClassProfileNAME VARCHAR(255),
        ClassLangName VARCHAR(255),
        EONAME VARCHAR(255),
        EOTYPENAME VARCHAR(255),
        EORegName VARCHAR(255),
        EOAreaName VARCHAR(255),
        EOTerName VARCHAR(255),
        EOParent VARCHAR(255),
        UkrTest VARCHAR(255),
        UkrTestStatus VARCHAR(255),
        UkrBall100 FLOAT,
        UkrBall12 FLOAT,
        UkrBall FLOAT,
        UkrAdaptScale VARCHAR(255),
        UkrPTName VARCHAR(255),
        UkrPTRegName VARCHAR(255),
        UkrPTAreaName VARCHAR(255),
        UkrPTTerName VARCHAR(255),
        histTest VARCHAR(255),
        HistLang VARCHAR(255),
        histTestStatus VARCHAR(255),
        histBall100 FLOAT,
        histBall12 FLOAT,
        histBall FLOAT,
        histPTName VARCHAR(255),
        histPTRegName VARCHAR(255),
        histPTAreaName VARCHAR(255),
        histPTTerName VARCHAR(255),
        mathTest VARCHAR(255),
        mathLang VARCHAR(255),
        mathTestStatus VARCHAR(255),
        mathBall100 FLOAT,
        mathBall12 FLOAT,
        mathBall FLOAT,
        mathPTName VARCHAR(255),
        mathPTRegName VARCHAR(255),
        mathPTAreaName VARCHAR(255),
        mathPTTerName VARCHAR(255),
        physTest VARCHAR(255),
        physLang VARCHAR(255),
        physTestStatus VARCHAR(255),
        physBall100 FLOAT,
        physBall12 FLOAT,
        physBall FLOAT,
        physPTName VARCHAR(255),
        physPTRegName VARCHAR(255),
        physPTAreaName VARCHAR(255),
        physPTTerName VARCHAR(255),
        chemTest VARCHAR(255),
        chemLang VARCHAR(255),
        chemTestStatus VARCHAR(255),
        chemBall100 FLOAT,
        chemBall12 FLOAT,
        chemBall FLOAT,
        chemPTName VARCHAR(255),
        chemPTRegName VARCHAR(255),
        chemPTAreaName VARCHAR(255),
        chemPTTerName VARCHAR(255),
        bioTest VARCHAR(255),
        bioLang VARCHAR(255),
        bioTestStatus VARCHAR(255),
        bioBall100 FLOAT,
        bioBall12 FLOAT,
        bioBall FLOAT,
        bioPTName VARCHAR(255),
        bioPTRegName VARCHAR(255),
        bioPTAreaName VARCHAR(255),
        bioPTTerName VARCHAR(255),
        geoTest VARCHAR(255),
        geoLang VARCHAR(255),
        geoTestStatus VARCHAR(255),
        geoBall100 FLOAT,
        geoBall12 FLOAT,
        geoBall FLOAT,
        geoPTName VARCHAR(255),
        geoPTRegName VARCHAR(255),
        geoPTAreaName VARCHAR(255),
        geoPTTerName VARCHAR(255),
        engTest VARCHAR(255),
        engTestStatus VARCHAR(255),
        engBall100 FLOAT,
        engBall12 FLOAT,
        engDPALevel VARCHAR(255),
        engBall FLOAT,
        engPTName VARCHAR(255),
        engPTRegName VARCHAR(255),
        engPTAreaName VARCHAR(255),
        engPTTerName VARCHAR(255),
        fraTest VARCHAR(255),
        fraTestStatus VARCHAR(255),
        fraBall100 FLOAT,
        fraBall12 FLOAT,
        fraDPALevel VARCHAR(255),
        fraBall FLOAT,
        fraPTName VARCHAR(255),
        fraPTRegName VARCHAR(255),
        fraPTAreaName VARCHAR(255),
        fraPTTerName VARCHAR(255),
        deuTest VARCHAR(255),
        deuTestStatus VARCHAR(255),
        deuBall100 FLOAT,
        deuBall12 FLOAT,
        deuDPALevel VARCHAR(255),
        deuBall FLOAT,
        deuPTName VARCHAR(255),
        deuPTRegName VARCHAR(255),
        deuPTAreaName VARCHAR(255),
        deuPTTerName VARCHAR(255),
        spaTest VARCHAR(255),
        spaTestStatus VARCHAR(255),
        spaBall100 FLOAT,
        spaBall12 FLOAT,
        spaDPALevel VARCHAR(255),
        spaBall FLOAT,
        spaPTName VARCHAR(255),
        spaPTRegName VARCHAR(255),
        spaPTAreaName VARCHAR(255),
        spaPTTerName VARCHAR(255),
        YEAR INTEGER
    )
        """
    }
}




def merge_dataframe_from_csv_files(csv_path_config, csv_openfile_options):
    dataframes = []

    for year in csv_path_config:
        path = csv_path_config[year]['path']
        encoding = csv_path_config[year]['encoding']
        df = pd.read_csv(path, encoding=encoding, decimal=',', nrows=1000, **csv_openfile_options)
        df['YEAR'] = year

        # Добавляем DataFrame в список dataframes
        dataframes.append(df)
        print(f'Read csv file for {year} year -  completed !')

    df = pd.concat(dataframes)
    df.index.name = 'ID'
    df = df.where((pd.notnull(df)), None)
    return df


def create_table(table_name, query, conn):
    cur = conn.cursor()

    cur.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = %s)", (table_name,))
    table_exists = cur.fetchone()[0]

    if not table_exists:
        cur.execute(query)
        conn.commit()
        print(f"Table {table_name} created")
    else:
        print(f"Table {table_name} already exists")

    cur.close()


def open_conn(db_config):
    check = 3
    while check != 0:
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                dbname=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            break
        except OperationalError:
            print( f"Failed to connect to the database {db_config['database']}. Retry attempt will be made {check} more time(s).")

            time.sleep(5)
            check -= 1
            if check == 0:
                raise
    return conn


def load_dataframe_to_postgresql(df: pd.DataFrame, table_name: str, conn: psycopg2.extensions.connection) -> int:
    with conn.cursor() as cursor:

        # Получить индекс последнего вставленного ряда
        get_last_idx_query = f"SELECT COUNT(*) FROM {table_name} "
        cursor.execute(get_last_idx_query)
        last_idx = cursor.fetchone()
        if last_idx:
            last_idx = last_idx[0]
        else:
            last_idx = 0
        print(f'Find last inserted index - {last_idx} ')

        # Вставка данных кусками по 1000 строк
        while last_idx < len(df):
            chunk_df = df.iloc[last_idx:last_idx + 1000]
            chunk_df = chunk_df.reset_index(drop=True)
            cols = chunk_df.columns.tolist()
            vals = ", ".join([f"%({col})s" for col in cols])
            insert_query = sql.SQL(
                f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({vals}) ON CONFLICT DO NOTHING")
            insert_data = [dict(row) for _, row in chunk_df.iterrows()]
            cursor.executemany(insert_query, insert_data)
            conn.commit()
            last_idx += 1000
            print(f'Last index updated to {last_idx}')
    conn.close()
    return len(df)



if __name__ == '__main__':

    start_time = time.time()
    merged_df = merge_dataframe_from_csv_files(CSV_CONFIG['PATH_CONFIG'], CSV_CONFIG['OPEN_CONFIG'])
    print('Dataset already imported')

    conn = open_conn(DB_CONFIG)
    print('Connection open')

    create_table(GENERAL_TABLE_NAME, SQL_PARAM['QUERY']['CREATE_TABLE'], conn)
    conn.close()
    print('General table created')

    print('Import to database started !')
    imported_rows = 0

    while imported_rows != len(merged_df):
        try:
            conn = open_conn(DB_CONFIG)
            imported_rows = load_dataframe_to_postgresql(merged_df, GENERAL_TABLE_NAME, conn)
        except psycopg2.OperationalError:
            print(f"Database unavailable. \nIf you have disabled it, please start it again. "
                  f"Reconnecting in 30 seconds.")
            time.sleep(30)  # ждем 30 секунд и повторяем проверку

        except Exception as e:
            print(e)
            raise

    print(f'Import completed ! \nImported rows - {imported_rows}')

    end_time = time.time()
    print("Program running time: %s seconds" % (end_time - start_time))