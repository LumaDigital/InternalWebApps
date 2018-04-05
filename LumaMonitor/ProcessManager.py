import subprocess
import os
import psutil
import sys
import logging
import traceback
import time

autostart_low_priority_app = False
low_priority_app_name = ""

wait_time = 30
current_time = 0


def process_count(name):
    count = 0
    for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
        if name == p.info['name']:
            count += 1
    return count

def process_running(name):
    try:
        "Return True if a process is found by the same name"
        for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
            if name == p.info['name']:
                return True
        return False
    except:
        e = sys.exc_info()[0]
        logging.error(traceback.format_exc())
        print "Error: %s" % e
        return False


def FavourProcess(high_priority_app, low_priority_app):
    global current_time
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
            start_Low_priority()
    return

def start_Low_priority():
    global current_time
    global wait_time

    if current_time == 0:
        current_time = time.time()
    elif current_time + wait_time <= time.time():
        subprocess.Popen("devcon disable =display", shell=True)
        time.sleep(5)
        subprocess.Popen("devcon enable =display", shell=True)
        time.sleep(5)
        start_process(low_priority_app_name)
        current_time = 0



def kill_process(name):
    os.system("taskkill /F /IM " + name)


def start_process(name):
    subprocess.Popen(name)



