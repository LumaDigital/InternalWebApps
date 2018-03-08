import LumaCommServer
from flask import Flask, request, jsonify
from flask import render_template
import json

server = LumaCommServer.LumaCommServer()
server.start_server()

farm_data = []
workstation_data = []

app = Flask(__name__)

print "Luma Monitor Server"


def get_serverdata():
    global farm_data
    global workstation_data

    farm_data = []
    workstation_data = []

    data = server.format_for_table()
    for item in data:
        if 'FARM' in item['Name']:
            farm_data.append(item)
        else:
            workstation_data.append(item)

@app.route("/workstations", methods=['POST', 'GET'])
def workstations():
    data = request.form

    if 'Action' in data:
        print data['Action'] + " : " + data['Machine']

    get_serverdata()

    return render_template('WorkstationStats.html', data=json.dumps(workstation_data))

@app.route("/farm", methods=['POST', 'GET'])
def farm():
    data = request.form

    if 'Action' in data:
        print data['Action'] + " : " + data['Machine']

    get_serverdata()

    return render_template('FarmStats.html', data=json.dumps(farm_data))


@app.route("/updatefarm", methods=['POST', 'GET'])
def updatefarm():
    data = request.form

    if 'Action' in data:
        print data['Action'] + " : " + data['Machine']

    get_serverdata()

    return jsonify(farm_data)

@app.route("/updateworkstations", methods=['POST', 'GET'])
def updateworkstations():
    data = request.form

    if 'Action' in data:
        print data['Action'] + " : " + data['Machine']

    get_serverdata()

    return jsonify(workstation_data)








