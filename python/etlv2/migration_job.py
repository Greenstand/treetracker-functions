import collections
from dotenv import load_dotenv
import logging
import os
import psycopg2
from psycopg2 import sql
import sys
from typing import List, Tuple, Any

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

src_db_info = {
    "host": src_db_host,
    "port": src_db_port,
    "dbname": src_db_name,
    "user": src_db_user,
    "password": src_db_password
}

# Database connection details for dbtwo

dst_db_info = {
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
        table_schema = [(row[0], row[2]) for row in cursor.fetchall()]
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


def register_all_udts(source_conn, dest_conn):
    query = """
    SELECT t.typname AS type_name, 
           n.nspname AS schema_name,
           array_agg(e.enumlabel ORDER BY e.enumsortorder) AS enum_labels
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    JOIN pg_enum e ON t.oid = e.enumtypid
    GROUP BY t.typname, n.nspname;
    """

    cursor = source_conn.cursor()
    cursor.execute(query)
    udt_info = cursor.fetchall()

    for type_name, schema_name, enum_labels in udt_info:
        full_type_name = f"{schema_name}.{type_name}"
        
        psycopg2.extensions.register_type(
            psycopg2.extensions.new_type(
                (source_conn.get_dsn_parameters()['dbname'] + '.' + full_type_name,),
                full_type_name,
                lambda value, cursor: value
            )
        )
    
    cursor.close()

    # Register the UDTs in the destination database
    for type_name, schema_name, enum_labels in udt_info:
        full_type_name = f"{type_name}"
        enum_lst = ', '.join([f"'{label}'" for label in enum_labels])
        
        create_enum_type_query = f"CREATE TYPE {full_type_name} AS ENUM ({enum_lst});"
        udt_query = f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{type_name}') THEN
                        {create_enum_type_query}
                        END IF;
                    END$$;
                    """
        dest_cursor = dest_conn.cursor()
        dest_cursor.execute(udt_query)
    dest_cursor.close()

# only fetch columns that are present in the source table
# transform the data fetched 
def fetch_and_transform(conn, table_name: str, src_table_columns: List[str], dest_table_columns: List[str], batch_size = 10 ** 6) -> List[tuple[Any, ...]]:
    """
        Only fetch columns that are present in BOTH the source table and the dest table
        For columns that only exists in the dest table but not in the source table, 
        we transform the data fetched from the source table to fit the dest table's schema by appending NULL values.
    """
    assert table_name in TABLES, "you must specify the tables you want to fetch in TABLES"
    res_data = []
    request_columns = [col for col in dest_table_columns if col in src_table_columns] # all columns that exist both in the src table and dest table
    with conn.cursor() as cursor:
        request_columns_str = ", ".join(request_columns) if request_columns else "*"
        query = f"SELECT {request_columns_str} FROM {table_name};"
        if entity_ids: # use the specified entity id as filter condition
            query = query[:-1] + " WHERE "
            filter_column = "id" if table_name == "entity" else "organization_id" if table_name == "planter" else "planter_id"
            entity_ids_str = ", ".join(map(str, entity_ids))
            query += f"{filter_column} IN ({entity_ids_str})"
            print(query)
        cursor.execute(query)
        while True:
            fetched_data = cursor.fetchmany(batch_size)
            if not fetched_data:
                break
            else:
                for data in fetched_data: # iterate over every row
                    transformed_data = []
                    i = j = 0
                    m, n = len(request_columns), len(dest_table_columns)
                    while i < m and j < n: # for every column of that row
                        if request_columns[i] == dest_table_columns[j]:
                            transformed_data.append(data[i])
                            i += 1
                            j += 1
                        else:
                            transformed_data.append(None)
                            j += 1
                    res_data.append(tuple(transformed_data))
    return res_data

def fetch_table_columns(conn, table_name: str) -> List[str]:
    with conn.cursor() as cursor:
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
        table_cols = [row[0] for row in cursor.fetchall()]
    return table_cols

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
        cols = ", ".join(col_names)
        placeholders = ", ".join(["%s"] * len(col_names))
        for d in data:
            insert_query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
            cur.execute(insert_query, d)
        conn.commit()
    
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logger.info("Starting the data migration job")
    src_conn = psycopg2.connect(**src_db_info)
    dest_conn = psycopg2.connect(**dst_db_info)
    register_all_udts(src_conn, dest_conn)

    entity_ids = [1]
    TABLES = ['entity', 'planter', 'trees']
    try:
        # the following is needed if we need to create user defined types that isn't present the the dest database
        # user_defined_types = fetch_user_defined_types(src_conn) 
        # create_user_defined_types(dest_conn, user_defined_types)
        for table_name in TABLES:
            src_table_columns = fetch_table_columns(src_conn, table_name) 
            dest_table_columns = fetch_table_columns(dest_conn, table_name)
            transformed_tuples = fetch_and_transform(src_conn, table_name, src_table_columns, dest_table_columns)
            insert_table_data(dest_conn, table_name, dest_table_columns, transformed_tuples)
    finally:
        src_conn.close()
        dest_conn.close()
