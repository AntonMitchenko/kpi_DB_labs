import os
import time
from pymongo import MongoClient
from sqlalchemy import create_engine, MetaData, Table
GENERAL_TABLE_NAME = "res_zno"

# DB_CONFIG = {'user': 'postgres',
#              'password': 'AI3006',
#              'host': 'localhost',
#              'port': 5432,
#              'database': 'zno'}

DB_CONFIG = {
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': os.getenv("POSTGRES_HOST"),
    'port': os.getenv("POSTGRES_PORT"),
    'database': os.getenv("POSTGRES_NAME")
}

start_time = time.time()


pg_engine = create_engine(f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
pg_connection = pg_engine.connect()
pg_metadata = MetaData(bind=pg_engine)


DB_CONFIG_MDB = {
    'host': "mongodb",
    'port': 27017,
    'database': "zno_result"
}

# Підключення до MongoDB
mongo_host = DB_CONFIG_MDB['host']
mongo_port = DB_CONFIG_MDB['port']
mongo_database = DB_CONFIG_MDB['database']
mongo_client = MongoClient(f'mongodb://{mongo_host}:{mongo_port}')
mongo_db = mongo_client[mongo_database]




print(f"Migration to mongo started")

def migrate_data(source_table, target_collection, chunk_size=10000):
    # Видаляємо всі документи з колекції перед міграцією
    target_collection.delete_many({})

    # Отримуємо метадані таблиці з PostgreSQL
    pg_table = Table(source_table, pg_metadata, autoload=True)

    # Виконуємо SELECT-запит до PostgreSQL та мігруємо дані в MongoDB
    documents = []
    select_query = pg_table.select()
    result_proxy = pg_connection.execute(select_query)
    for row in result_proxy:
        document = {}

        # Додаємо всі колонки в словник document
        for column in pg_table.columns:
            column_name = column.name
            if column_name == 'ID':
                document['_id'] = row[column_name]
            else:
                document[column_name] = row[column_name]

        documents.append(document)

        if len(documents) == chunk_size:
            target_collection.insert_many(documents)
            documents = []

    if documents:
        target_collection.insert_many(documents)

    print(f"{source_table} already migrated")



# Міграція educational_institutions
educational_institutions = mongo_db['educational_institutions']
migrate_data('educational_institutions', educational_institutions)

# Міграція territories
territory_mongo = mongo_db['territory_mongo']
migrate_data('territories', territory_mongo)

# Міграція participants
participant_mongo = mongo_db['participant_mongo']
migrate_data('participants', participant_mongo)

# Міграція testings
testing_mongo = mongo_db['testing_mongo']
migrate_data('testings', testing_mongo)

# Міграція points_of_observation
point_of_observation_mongo = mongo_db['point_of_observation_mongo']
migrate_data('points_of_observation', point_of_observation_mongo)




mongo_client.close()

elapsed_time = time.time() - start_time
print(f"Migration completed in {elapsed_time} seconds")