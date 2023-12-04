import unittest
from transfer_wallet import transfer_wallet

class Test_Transfer(unittest.TestCase):
    def test(self):
        import psycopg2
        # read env variables DB_URL
        import os
        print("transfer data")
        # read env variables DB_URL
        DB_SOURDE_URL = os.environ['DB_SOURDE_URL']
        DB_DESTINATION_URL  = os.environ[' DB_DESTINATION_URL ']
        
        # need organization id
        print("DB_SOURDE_URL:", DB_SOURDE_URL)
        print("DB_DESTINATION_URL:",  DB_DESTINATION_URL)
        src_conn = psycopg2.connect(DB_SOURDE_URL, sslmode='require')
        dest_conn = psycopg2.connect( DB_DESTINATION_URL , sslmode='require')
        transfer_wallet(dest_conn,src_conn, 11, action = False)

        return 
    
if __name__ == '__main__':
   
    unittest.main()