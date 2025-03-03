import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE X1BI23EC_SEM_1")
conn.commit()
conn.close()