import sqlite3
from prettytable import PrettyTable

class RDB:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS records
                            (idx INTEGER PRIMARY KEY, user TEXT, spender TEXT, houmuch REAL, cid TEXT)''')
        self.conn.commit()

    def insert_record(self, user, spender, houmuch, cid):
        self.cursor.execute('''INSERT INTO records (user, spender, houmuch, cid) VALUES (?, ?, ?, ?)''',
                            (user, spender, houmuch, cid))
        self.conn.commit()

    def load_records(self):
        self.cursor.execute('''SELECT * FROM records''')
        return self.cursor.fetchall()

    def get_table_as_string(self):
        records = self.load_records()
        table = PrettyTable(["Index", "User", "Spender", "Amount", "CID"])
        for record in records:
            table.add_row(record)    
        return table
    

    def close_connection(self):
        self.conn.close()
