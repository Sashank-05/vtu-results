import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("DROP TABLE BI22CD_SEM_4")
conn.commit()
conn.close()