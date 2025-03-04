import sqlite3

# Source and destination database file paths
source_db = "t.db"
destination_db = "database.db"
table_name = "BI23CD_SEM_3"  # Change this to the actual table name

# Connect to the destination database
dest_conn = sqlite3.connect(destination_db)
dest_cursor = dest_conn.cursor()

# Attach the source database
dest_cursor.execute(f"ATTACH DATABASE '{source_db}' AS src_db")

# Copy the table structure and data to the destination DB
dest_cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM src_db.{table_name}")

# Commit and close
dest_conn.commit()
dest_conn.close()

print(f"Table '{table_name}' copied successfully from {source_db} to {destination_db}.")
