from flask import Flask, request
from flask import render_template
import threading
import time
import os
import DataCrawler

import timeit


app = Flask(__name__)
print "Render Monitor Server"

@app.route("/", methods=['GET'])
def dashboard():
    return render_template('Dashboard.html', data=DataCrawler.data, time=DataCrawler.updated_at, frames_summary=DataCrawler.current_frame_total_summary, playouts_summary=DataCrawler.current_playouts_total_summary, average_frame_time=DataCrawler.average_render_time, remaining_time=DataCrawler.remaining_render_time)

@app.route("/", methods=['POST'])
def action():

    data = request.form
    print data.keys()

    if 'action' in data.keys():
        if data['action'] == "Delete":
            if os.path.exists(data['path']):
                os.remove(data['path'])

    return render_template('Dashboard.html', data=DataCrawler.data, time=DataCrawler.updated_at, frames_summary=DataCrawler.current_frame_total_summary, playouts_summary=DataCrawler.current_playouts_total_summary, average_frame_time=DataCrawler.average_render_time, remaining_time=DataCrawler.remaining_render_time)

@app.route("/detail", methods=['GET'])
def detail():
    playout_name = str(request.args["playout"])
    return render_template('PlayoutDetail.html', data=DataCrawler.data, time=DataCrawler.updated_at, frames_summary=DataCrawler.current_frame_total_summary, playouts_summary=DataCrawler.current_playouts_total_summary, Playout=playout_name, average_frame_time=DataCrawler.average_render_time, remaining_time=DataCrawler.remaining_render_time)

@app.route("/stats", methods=['GET'])
def stats_dashboard():
    return render_template('StatsDashboard.html', log=DataCrawler.log_text)

@app.route("/log", methods=['GET'])
def log():
    if "path" in request.args:
        content = open(request.args["path"], "r").read()
        return "<pre>" + content + "</pre>"


def update_data():

    while True:
        start = timeit.default_timer()
        try:
            print "getting data"
            DataCrawler.update()
            print "done"
        except Exception, err:
            print "Error Occured: " + str(err)

        stop = timeit.default_timer()
        print stop - start
        time.sleep(30)



#######################

thread = threading.Thread(target=update_data, args=())
thread.daemon = True
thread.start()
