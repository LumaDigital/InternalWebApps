import traceback
import Monitor
import LumaCommServer
import json
import time
import logging
import sys
import itertools
import glob
import Tray
import ProcessManager

keep_running = True

def shutdown(sysTrayIcon):
    logging.info("Shutting Down")
    global keep_running
    keep_running = False

# Read Config values
config_file = json.load(open('config.json'))
host = config_file['Config']['Server']
port = config_file['Config']['Port']
processes = config_file['Config']['Processes']
update_frequency = config_file['Config']['Update_Frequency_Seconds']

ProcessManager.autostart_low_priority_app = config_file['Config']['AutoStart_Miner']
ProcessManager.low_priority_app_name = config_file['Config']['Miner_Path']
miner_process_name = config_file['Config']['Miner_Process_Name']
miner_pause_when_running = config_file['Config']['Miner_Pause_When_Running']



# Start Log file
logging.basicConfig(filename='main.log', filemode='w', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info("Configured to send data to " + host + " on port " + str(port))
# sys.stdout = open('stdout.txt', 'w')


# Start Server Comms
logging.info("Attempting to start server")

server = LumaCommServer.LumaCommServer(host, port)

# Setting up System Tray Icon
icons = itertools.cycle(glob.glob('*.ico'))
hover_text = "Luma Monitor"

logging.info("Setting up System Tray")
menu_options = ()

try:
    tray = Tray.SysTrayIcon(icons.next(), hover_text, menu_options, on_quit=shutdown, default_menu_index=1)
    logging.info("System Tray Done")

except:
    e = sys.exc_info()[0]
    logging.warning("Error setting up system tray: %s" % e);
    logging.error(traceback.format_exc())
    shutdown()


logging.info("Starting Monitor")

# Main Loop
while keep_running:
    try:
        json_data = Monitor.generate_json(processes)
        ProcessManager.FavourProcess(miner_pause_when_running, miner_process_name)

        tray.update()
        server.send_update(json_data)
        time.sleep(update_frequency)
    except:
        e = sys.exc_info()[0]
        logging.error(traceback.format_exc())
        print "Error: %s" % e
        break

logging.info("Monitor Stopped")
