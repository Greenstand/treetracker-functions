from dotenv import load_dotenv
from typing import List, Tuple, Any
# from apscheduler.schedulers.blocking import BlockingScheduler
import os
import psycopg2
from psycopg2 import sql
import logging
# import pandas as pd
# import re
# from decimal import Decimal
import collections
import sys
import configparser

load_dotenv(override=True)

src_db_host = os.environ.get("SRC_DB_HOST")
src_db_port = os.environ.get("SRC_DB_PORT")
src_db_name = os.environ.get("SRC_DB_NAME")
src_db_user = os.environ.get("SRC_DB_USER")
src_db_password = os.environ.get("SRC_DB_PASSWORD")

dest_db_host = os.environ.get("DEST_DB_HOST")
dest_db_port = os.environ.get("DEST_DB_PORT")
dest_db_name = os.environ.get("DEST_DB_NAME")
dest_db_user = os.environ.get("DEST_DB_USER")
dest_db_password = os.environ.get("DEST_DB_PASSWORD")

# Database connection details for dbone
<<<<<<< Updated upstream
src_db_config = {
=======
src_db_info = {
>>>>>>> Stashed changes
    "host": src_db_host,
    "port": src_db_port,
    "dbname": src_db_name,
    "user": src_db_user,
    "password": src_db_password
}

# Database connection details for dbtwo
<<<<<<< Updated upstream
dst_db_config = {
=======
dst_db_info = {
>>>>>>> Stashed changes
    "host": dest_db_host,
    "port": dest_db_port,
    "dbname": dest_db_name,
    "user": dest_db_user,
    "password": dest_db_password
}

def fetch_table_schema(src_db_conn, table_name) -> List[Tuple[str, str]]: # returns a list of (column_name, type) tuples
    with src_db_conn.cursor() as cursor:
        cursor.execute(sql.SQL("""
            SELECT 
                c.column_name, 
                c.data_type,
                CASE 
                    WHEN c.data_type = 'USER-DEFINED' THEN 
                        (SELECT t.typname FROM pg_catalog.pg_type t WHERE t.oid = a.atttypid)
                    ELSE c.data_type 
                END as actual_data_type
            FROM 
                information_schema.columns c
                JOIN pg_catalog.pg_class r ON r.relname = c.table_name
                JOIN pg_catalog.pg_attribute a ON a.attrelid = r.oid AND a.attname = c.column_name
            WHERE 
                c.table_name = %s
            ORDER BY c.ordinal_position;
        """), [table_name])
        # cursor.execute(sql.SQL("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s"), [table_name])
        table_schema = [(row[0], row[1]) for row in cursor.fetchall()]
    print(table_schema)
    return table_schema

def fetch_user_defined_types(src_db_conn):
    with src_db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT pg_type.typname, pg_enum.enumlabel FROM pg_type JOIN pg_enum ON pg_enum.enumtypid = pg_type.oid;
            """)
        types = cursor.fetchall()
    user_defined_types = collections.defaultdict(list)
    for type_name, enum_label in types:
        user_defined_types[type_name].append(enum_label)

    return user_defined_types

def create_user_defined_types(dest_db_conn, user_defined_types):
    with dest_db_conn.cursor() as cursor:
        for type_name, enum_labels in user_defined_types.items():
            enum_labels = list(set(enum_labels))
            # print(type_name, enum_labels)
            check_type_query = sql.SQL("SELECT 1 FROM pg_type WHERE typname = %s;")
            cursor.execute(check_type_query, (type_name,))
            if not cursor.fetchone():
                create_type_query = sql.SQL("""
                    CREATE TYPE {} AS ENUM ({});
                """).format(
                    sql.Identifier(type_name), 
                    sql.SQL(', ').join(sql.Literal(label) for label in enum_labels)
                )
                cursor.execute(create_type_query)

    dest_db_conn.commit()

def fetch_table_data(conn, table_name: str, batch_size = 10 ** 6) -> Tuple[List[tuple[Any, ...]], List[str]]:
    logger.info(f"Reading from the {table_name} table from the source db")
    data = []
    with conn.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 2").format(sql.Identifier(table_name)))
        col_names = [desc[0] for desc in cursor.description]
        while True:
            fetched_data = cursor.fetchmany(batch_size)
            if not fetched_data:
                break
            else:
                data.append(fetched_data)
    return data, col_names

def create_table(dst_db_conn, table_name, table_schema) -> None:
    with dst_db_conn.cursor() as cursor:
        create_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
        n = len(table_schema)
        for i in range(n):
            col_name, t = table_schema[i]
            if i != n - 1:
                create_query += f"{col_name} {t}, "
            else:
                create_query += f"{col_name} {t}"
        create_query += ");"
        cursor.execute(create_query)
        dst_db_conn.commit()

def insert_table_data(conn, table_name, col_names, data) -> None:
    with conn.cursor() as cur:
        insert_query = sql.SQL("INSERT INTO {} VALUES ({})").format(
            sql.SQL(table_name),
            sql.SQL(', ').join(sql.Placeholder() for _ in col_names)
        )
        print(table_name)
        print(col_names)
        cur.executemany(insert_query, data[0])
    conn.commit()

# def migrate_table(source_conn, dest_conn, table_name) -> None:
#     data, colnames = fetch_table_data(source_conn, table_name)
#     create_table(dest_conn, table_name, colnames)
#     insert_table_data(dest_conn, table_name, colnames, data)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logger.info("Starting the data migration job")
    src_conn = psycopg2.connect(**src_db_info)
    dest_conn = psycopg2.connect(**dst_db_info)
    try:
        # user_defined_types = fetch_user_defined_types(src_conn)
        # create_user_defined_types(dest_conn, user_defined_types)
        for table_name in ['entity', 'planter', 'trees']:
            data_tuples, col_names = fetch_table_data(src_conn, table_name)
            table_schema = fetch_table_schema(src_conn, table_name)
            # create_table(dest_conn, table_name, table_schema) # create table in the dest db
            col_names = [elem[0] for elem in table_schema]
            insert_table_data(dest_conn, table_name, col_names, data_tuples)
    finally:
        src_conn.close()
        dest_conn.close()
