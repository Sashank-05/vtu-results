import logging
import logging
import threading

from flask import Flask, render_template, jsonify, redirect, url_for, request
from flask_socketio import SocketIO

from new_helpers import dbhandler, formats
from new_helpers import fetchdata

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s - '
                                               '[%(filename)s:%(lineno)d in %(funcName)s]')

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
socketio = SocketIO(app)
db = dbhandler.DBHandler()

# set static folder
app.static_folder = 'static'
# url for static files = /static + filename

db.connect()

apiv1 = '/api/v1/'


@app.route('/')
def home():
    return render_template("home.html")


@app.route(apiv1 + "export/<string:type>")
def export(type):
    if type == "excel":
        # return a file to download
        raise NotImplementedError
    else:
        return jsonify({"error": "Type not Found"})


@app.route(apiv1 + 'student/<string:usn>', methods=['GET'])
def get_student(usn):
    table = []
    data = []
    try:
        for i in range(1, 9):
            print(i)
            try:
                x, y = formats.neat_marks(i, usn)
                table.append(x)
                data.append(y)
            except Exception as e:
                print(e)

    except Exception as e:
        # log with traceback
        logging.error(f"Error fetching student data: {e}", exc_info=True)
        table.append("<h2> no data </h2>")
        data += [["NAN", "NAN"]]
    return jsonify(table, data)


@app.route(apiv1 + '<string:id>/<string:sem>', methods=['GET'])
def get_sem_marks(id, sem):
    try:
        sem_marks = db.get_semester_marks(id, sem)
        columns = db.get_columns(f"{id}_SEM_{sem}")
        return jsonify(sem_marks, columns)
    except Exception as e:
        print(e)
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
    usn_prefix = data.get('usn_prefix')
    custom_url = data.get('custom_url')
    sem = data.get('sem')
    end_usn = data.get('end_usn')
    num_threads = data.get('num_threads', 4)

    if not usn_prefix or not custom_url or not sem or not sem.isdigit() or not end_usn or not end_usn.isdigit():
        return jsonify({'success': False, 'error': 'Please provide valid data'}), 400

    try:
        handler = fetchdata.ThreadManager(
            custom_url, usn_prefix, f"{usn_prefix[1:]}_SEM_{sem}", end_usn=end_usn,
            num_threads=int(num_threads), socketio=socketio
        )

        threading.Thread(target=handler.run_threads).start()
        # fetchdata.save_to_db(f"{usn_prefix[1:]}_SEM_{sem}")

        return jsonify({'success': True}), 200

    except ValueError as ve:
        app.logger.error(f"ValueError: {ve}", exc_info=True)
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        app.logger.error(f"Exception: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500


@app.route('/live')
def live_scrape():
    return render_template("live.html")


@socketio.on('connect')
def handle_connect():
    app.logger.info('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    app.logger.info('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, debug=True, port=8000)
