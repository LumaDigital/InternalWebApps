from flask import Flask, request
from flask import render_template
import threading
import time
import os
import DataCrawler
import sys


app = Flask(__name__)
print "Render Monitor Server"

@app.route("/", methods=['GET'])
def dashboard():
    return render_template('Dashboard.html', data=DataCrawler.data, time=DataCrawler.updated_at, summary=DataCrawler.current_total_summary)

@app.route("/", methods=['POST'])
def action():

    data = request.form
    print data.keys()

    if 'action' in data.keys():
        if data['action'] == "Delete":
            if os.path.exists(data['path']):
                os.remove(data['path'])

    return render_template('Dashboard.html', data=DataCrawler.data, time=DataCrawler.updated_at, summary=DataCrawler.current_total_summary)

@app.route("/log", methods=['GET'])
def log():
    if "path" in request.args:
        content = open(request.args["path"], "r").read()
        return "<pre>" + content + "</pre>"

def update_data():

    while True:

        try:
            print "getting data"
            DataCrawler.update()
            print "done"
        except:
            print "Error Occured", sys.exc_info()[1]

        time.sleep(30)



#######################

thread = threading.Thread(target=update_data, args=())
thread.daemon = True
thread.start()
