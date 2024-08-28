from flask import Flask, render_template, jsonify, redirect, url_for, request

from helper import dbhandler, test, threadedgetdata

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
    table = []
    data = []
    try:
        for i in range(1, 9):
            x, y = test.neat_marks(i, usn)
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
        # if error is table not found then redirect to scrape page
        if "no such table" in str(e):
            return redirect(url_for('scrape', usn_prefix=id))
        else:
            return jsonify({'error': str(e)}), 500


@app.route('/scrape')
def scrape():
    return render_template("scrape.html")


@app.route(apiv1 + 'scrape', methods=['POST'])
def scrape_student():
    data = request.json
    usn_prefix = data['usn_prefix']
    custom_url = data.get('custom_url')
    sem = data.get('sem')
    end_usn = data.get('end_usn')
    num_threads = data.get('num_threads', 4)

    if (not custom_url or not usn_prefix or not custom_url or not sem or not sem.isdigit() or not end_usn or
            not end_usn.isdigit()):
        return jsonify({'success': False, 'error': 'Please provide valid data'}), 400

    try:
        handler = threadedgetdata.ThreadManager(custom_url, usn_prefix, f"{usn_prefix[1::]}_SEM_{sem}", end_usn, num_threads=num_threads)
        handler.run_threads()

        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
