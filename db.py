import sqlite3
from prettytable import PrettyTable
import json
import collections
from icecream import ic

class RDB:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS records
                            (idx INTEGER PRIMARY KEY, user TEXT, spender TEXT, houmuch REAL, perperson REAL, cid TEXT, rezhesab TEXT)''')
        self.conn.commit()

    def insert_record(self, user, spender, houmuch, perperson, cid, rezhesab_dict):
        rezhesab_text = json.dumps(rezhesab_dict)  # Serialize dictionary to JSON string
        self.cursor.execute('''INSERT INTO records (user, spender, houmuch, perperson, cid, rezhesab) VALUES (?, ?, ?, ?, ?, ?)''',
                            (user, spender, houmuch, perperson, cid, rezhesab_text))
        self.conn.commit()

    def load_records(self):
        self.cursor.execute('''SELECT * FROM records''')
        return self.cursor.fetchall()

    def get_table_as_string(self):
        records = self.load_records()

        keys_set = set()
        for record in records:
            keys_set.update(json.loads(record[-1]).keys())
        keys = list(keys_set)

        # reset total for each team
        final_hesab_team = {}
        for key in keys:
            final_hesab_team[key] = 0

        total_amount = 0
        total_perperson = 0
        table = PrettyTable(["Index", "User", "Spender", "Amount", "Perperson"] + keys)
        for record in records[:-1]:
            Index, User, Spender, Amount, Perperson = record[:5]
            total_amount += Amount
            total_perperson += Perperson
            rezhesab = json.loads(record[-1])
            hesab = tuple(map(lambda key: "{:.2f}".format(rezhesab[key]), keys))
            table.add_row((Index, User, Spender, Amount, round(Perperson, 2)) + hesab)  # Exclude the "rezhesab" column
            for key in keys:
                final_hesab_team[key] += rezhesab[key]

        if records:
            record = records[-1]
            Index, User, Spender, Amount, Perperson = record[:5]
            total_amount += Amount
            total_perperson += Perperson
            rezhesab = json.loads(record[-1])
            hesab = tuple(map(lambda key: "{:.2f}".format(rezhesab[key]), keys))
            table.add_row((Index, User, Spender, Amount, round(Perperson, 2)) + hesab, divider=True)  # Exclude the "rezhesab" column
            for key in keys:
                final_hesab_team[key] += rezhesab[key]

        final_hesab_team_row = [str(round(float(final_hesab_team[key]), 1)) for key in keys]
        table.add_row(["-", "-", "-", total_amount, total_perperson] + final_hesab_team_row)

        return table

    def retrieve_rezhesab(self, index):
        self.cursor.execute('''SELECT rezhesab FROM records WHERE idx = ?''', (index,))
        rezhesab_text = self.cursor.fetchone()[0]
        return json.loads(rezhesab_text)  # Deserialize JSON string to dictionary

    def close_connection(self):
        self.conn.close()
