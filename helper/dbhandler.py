import sqlite3


class DBHandler:
    def __init__(self, db_path='database.db', student_db_path='students.db'):
        self.db_path = db_path
        self.student_db_path = student_db_path
        self.initialize_database()
        self.initialize_student_database()

    def connect(self, db_path):
        return sqlite3.connect(db_path)

    def initialize_database(self):
        create_branch_table_query = """
        CREATE TABLE IF NOT EXISTS branches (
            branch_id TEXT PRIMARY KEY,
            branch_name TEXT NOT NULL
        );
        """
        create_marks_table_query = """
        CREATE TABLE IF NOT EXISTS marks (
            usn TEXT,
            branch_id TEXT,
            semester INTEGER,
            subject TEXT,
            marks INTEGER,
            FOREIGN KEY(branch_id) REFERENCES branches(branch_id)
        );
        """
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(create_branch_table_query)
        cursor.execute(create_marks_table_query)
        conn.commit()
        conn.close()

    def initialize_student_database(self):
        create_student_table_query = """
        CREATE TABLE IF NOT EXISTS students (
            usn TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            branch_id TEXT,
            FOREIGN KEY(branch_id) REFERENCES branches(branch_id)
        );
        """
        conn = self.connect(self.student_db_path)
        cursor = conn.cursor()
        cursor.execute(create_student_table_query)
        conn.commit()
        conn.close()

    def get_student_marks(self, usn):
        query = """
        SELECT * FROM marks
        WHERE usn = ?
        """
        conn = self.connect(self.student_db_path)
        cursor = conn.cursor()
        cursor.execute(query, (usn,))
        result = cursor.fetchall()
        conn.close()
        return result

    def get_branch_list(self, branch_id):
        query = """
        SELECT * FROM branches
        WHERE branch_id = ?
        """
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, (branch_id,))
        result = cursor.fetchall()
        conn.close()
        return result

    def get_semester_marks(self, branch_id, sem):
        query = """
        SELECT * FROM marks
        WHERE branch_id = ? AND semester = ?
        """
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, (branch_id, sem))
        result = cursor.fetchall()
        conn.close()
        return result
