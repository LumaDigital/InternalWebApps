import json
import os

class JobInfo:

    _type = "No Type"
    _name = "No Name"
    _status = "No Status"
    _time = "No Time"
    _agent = "No Agent"
    _filename = "No File"
    _logfile = "No File"
    _frame = 0
    _subjobs = []

    def __init__(self):
        return
        # , jobtype, name, status, time, agent):
        # self._type = jobtype
        # self._name = name
        # self._status = status
        # self._time = time
        # self._agent = agent


    def create_from_file(self, filename):
        data = json.load(open(filename))

        self._filename = filename.replace("\\", "/")

        if data['_job_state'] == 0:
            self._status = "None"
        elif data['_job_state'] == 1:
            self._status = "Busy"
        elif data['_job_state'] == 2:
            self._status = "Done"
        elif data['_job_state'] == 3:
            self._status = "Error"
        else:
            self._status = "Error"

        m, s = divmod(data['_elapsed_time_sec'], 60)
        h, m = divmod(m, 60)
        self._time = "%d:%02d:%02d" % (h, m, s)

        self._agent = data['_agent']

        if "AnimationRecordingInput" in filename:
            self._type = "Playout"
            name = os.path.basename(filename)
            self._name = name.split(".")[0]

        elif "AnimationRecordingOutput" in filename:
            self._type = "MainClip"
            name = os.path.basename(filename)
            name = name.split(".")
            self._name = name[0] + " Main Clip"

        elif "SplitRenderingOutput" in filename:
            self._type = "SubClip"
            name = os.path.basename(filename)
            name = name.split(".")
            self._name = "Sub Clip " + name[2]

        elif "RenderingOutput" in filename:
            self._type = "Render"
            name = os.path.basename(filename)
            self._name = name.split(".")[0]

        elif "VideoEncodingInput" in filename:
            self._type = "Video"
            name = os.path.basename(filename)
            self._name = name.split(".")[0]

        self._logfile = self._filename.replace(".job", ".log")
        if not os.path.isfile(self._logfile):
            self._logfile = "No File"


        self._subjobs = []

    def print_data(self):
        print "Type: " + self._type
        print "Name: " + self._name
        print "Status: " + self._status
        print "Time: " + str(self._time)
        print "Agent: " + self._agent
        print "Sub Jobs: "

        for job in self._subjobs:
            subdata = job.print_data()
            print "\t\n" + str(subdata)
            print "\n"

    def add_job(self, job):
        self._subjobs.append(job)

    def add_jobs(self, jobs):
        self._subjobs = jobs


    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)