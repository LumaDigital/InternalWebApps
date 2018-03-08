import subprocess
import os
import psutil

autostart_low_priority_app = False
low_priority_app_name = ""

def process_running(name):
    "Return True if a process is found by the same name"
    for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
        if name == p.info['name']:
            return "True"
    return "False"


def FavourProcess(high_priority_app, low_priority_app):

    # print "checking processes"
    high_running = process_running(high_priority_app) == "True"
    low_running = process_running(low_priority_app) == "True"
    # print "High: " + str(high_running)
    # print "Low: " + str(low_running)

    if high_running and low_running:
        kill_process(low_priority_app)

    elif not high_running and not low_running:
        if autostart_low_priority_app:
            start_process(low_priority_app_name)
    return


def kill_process(name):
    os.system("taskkill /F /IM " + name)


def start_process(name):
    subprocess.Popen(name)



