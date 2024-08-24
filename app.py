from flask import Flask, render_template, jsonify

from helper import dbhandler,test

app = Flask(__name__)

db = dbhandler.DBHandler()

db.connect()

apiv1 = '/api/v1/'


@app.route('/')
def home():
    return render_template("home.html")

"""@app.route(apiv1 + 'student/<string:usn>', methods=['GET'])
def get_student(usn):
    
    apiv1/student/1BI23CD001

    Get's the student's marks card from 1st to 8th semester

    
    try:
        student_marks = dict()
        cols = []
        for i in range(1, 8 + 1):
            try:
                student_marks[i] = list(db.get_student_marks("BI23CD", i, usn))
                cols.append(db.get_columns(f"BI23CD_SEM_{i}"))
                print(student_marks, cols)
            except Exception as e:
                if "no such table" in str(e):
                    pass
                else:
                    return jsonify({'error': str(e)}), 500
        return jsonify(student_marks, cols), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500"""


@app.route(apiv1 + 'student/<string:usn>', methods=['GET'])
def get_student(usn):
    try:
        table=[]
        data=[]
        for i in range(1,9):
            x,y=test.neat_marks(i,usn)
            table.append(x)
            data.append(y)
    except:
        pass 
    return jsonify(table, data)
 

@app.route(apiv1 + '<string:id>/<string:sem>', methods=['GET'])
def get_sem_marks(id, sem):
    """

    apiv1/1BI23CD/1

    returns the semester marks of all students belonging to 1BI23CD

    """
    try:
        sem_marks = db.get_semester_marks(id, sem)
        columns = db.get_columns(f"BI23CD_SEM_{sem}")

        return jsonify(sem_marks, columns)
    except Exception as e:
        # if error is table not found then scrape the page
        if "no such table" in str(e):
            return jsonify({'message': 'Scraping the page'}), 200
        else:
            return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
