from flask import Flask, render_template, jsonify
from helper import dbhandler

app = Flask(__name__)

db = dbhandler.DBHandler()

apiv1 = '/api/v1/'


@app.route('/')
def home():
    return render_template("home.html")


@app.route(apiv1 + 'student/<string:usn>', methods=['GET'])
def get_student(usn):
    """
    apiv1/1BI23CD001

    Get's the student's marks card from 1st to 8th semester

    """
    try:
        student_marks = db.get_student_marks(usn)
        return jsonify(student_marks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route(apiv1 + '<string:id>', methods=['GET'])
def get_branchlist(id):
    """
    apiv1/1BI23CD

    23 - year
    CD - branch

    returns the 1BI23CD table from sql
    """
    try:
        branch_list = db.get_branch_list(id)
        return jsonify(branch_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route(apiv1 + '<string:id>/<string:sem>', methods=['GET'])
def get_sem_marks(id, sem):
    """

    apiv1/1BI23CD/1

    returns the 1st semester marks of all students belonging to 1BI23CD

    """
    try:
        sem_marks = db.get_semester_marks(id, sem)
        return jsonify(sem_marks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
