import sqlite3 

class db_handler:
    def __init__(self, db_path='database.db'):
        self.db_path=db_path

    def connect(self, db_path):
        return sqlite3.connect(db_path)
        
    def create_table_cloumns(self,sub_columns:list): #table name also should be a parameter which should be taken from user
        sql_create_table="""CREATE TABLE BI23CD_SEM_1(
                    USN VARCHAR(12),
                    NAME VARCHAR(25))
            """
        connection=self.connect(self.db_path)
        cur=connection.cursor()
        cur.execute(sql_create_table)
        connection.commit()

        for sub in sub_columns:
            sql = f"ALTER TABLE BI23CD_SEM_1 ADD {sub} VARCHAR(100);"
            cur.execute(sql)
            connection.commit()

        connection.close()

    def push_data_into_table(self, inte: list, ext: list,  other: list):
        sql = """INSERT INTO BI23CD_SEM_1 VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )"""
        values = (other[0], other[1], inte[0], ext[0], inte[1], ext[1], inte[2], ext[2], 
              inte[3], ext[3], inte[4], ext[4], inte[5], ext[5], inte[6], ext[6],
              inte[7], ext[7],  other[2], other[3], other[4])
        connection=self.connect(self.db_path)
        cur=connection.cursor()
        cur.execute(sql, values)
        connection.commit()


        
        



    


