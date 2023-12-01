import psycopg2

def transfer_wallet(dest_conn,src_conn, wallet_id, action = False):
    """
    transport the data in our prod database that belongs to a specified wallet on Greenstand, and do some transform, then dump it into our dev database.

    The data that need to be transported are:

    Info of this wallet
    Tokens belong to this wallet
    Tree linked to all tokens above
 
    Args:
        target (string): The target database URL.
        source (string): The source database URL.
        wallet_id (int): The id of the desired wallet.
        action(boolean):Whether to update the database when the inserted row already exists.
 
    Returns:
        None.
    """

    src_cur = src_conn.cursor()
    dest_cur = dest_conn.cursor()


    def insert_or_update(table_name, columns, data, dest_cur, dest_conn, action=False, conflict_column='id'):
        """Inserts or updates records in the specified table.

            Args:
                table_name (string): The target table name.
                column(string list): The column names of target table.
                data (string list): The data to insert
                action(boolean): Update OR do nothing when there is duplicate
        
            Returns:
                None.
        
        """
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        update_statements = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns])

        if action:
            #if action == True, update the database if row already exists

            query = f"""
                INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})
                ON CONFLICT ({conflict_column}) DO UPDATE SET {update_statements};
            """
        else:
            query = f"""
                INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})
                ON CONFLICT ({conflict_column}) DO NOTHING;
            """
        dest_cur.executemany(query, data)
        dest_conn.commit()
        return
    
    src_cur.execute("SELECT * FROM wallet WHERE id = %s;", (wallet_id,))
    wallet_info = src_cur.fetchone()
    wallet = wallet_info[0]

    if wallet:
        wallet_columns = [desc[0] for desc in src_cur.description]
        insert_or_update("wallet", wallet_columns, [wallet_info], dest_cur, dest_conn, action=action)
    else:
        print("No such wallet")
        return

    src_cur.execute("SELECT * FROM token WHERE wallet_id = %s", (wallet_id,))
    token_data = src_cur.fetchall()
    token_columns = [desc[0] for desc in src_cur.description]
    insert_or_update("token", token_columns, token_data, dest_cur, dest_conn, action=action)

    for token in token_data:
        token_id = token[0]
        tree_id = token[9]
        src_cur.execute("SELECT * FROM trees WHERE token_id = %s", (token_id,))
        trees_data = src_cur.fetchall()
        tree_columns = [desc[0] for desc in src_cur.description]
        insert_or_update("trees", tree_columns, trees_data, dest_cur, dest_conn, action=action)
    
    src_cur.close()
    dest_cur.close()
    src_conn.close()
    dest_conn.close()
    return