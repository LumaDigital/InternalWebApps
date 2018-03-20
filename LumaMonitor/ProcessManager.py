import subprocess
import os
import psutil

autostart_low_priority_app = False
low_priority_app_name = ""


def process_count(name):
    count = 0
    for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
        if name == p.info['name']:
            count += 1
    return count

def process_running(name):
    "Return True if a process is found by the same name"
    for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
        if name == p.info['name']:
            return True
    return False


def FavourProcess(high_priority_app, low_priority_app):
    high_running = False
    low_running = False

    # print "checking processes"
    # Check if low priority process is running
    low_running = process_running(low_priority_app)

    # Low priority process is running, so check if any high priority ones are running as well
    for process_name in high_priority_app:
        if process_running(process_name):
            high_running = True
            break

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



