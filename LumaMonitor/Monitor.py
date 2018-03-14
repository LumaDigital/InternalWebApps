import wmi
import os
import socket
import time
import json

import ProcessManager

w = wmi.WMI(namespace="root\OpenHardwareMonitor")


def get_cpu_temp():
    temperature_info = w.Sensor()
    for sensor in temperature_info:
        if sensor.SensorType == u'Temperature' and sensor.Name == u'CPU Core #1':
            cpu_sensor = sensor
            return cpu_sensor.Value


def get_gpu_temp():
    temperature_info = w.Sensor()
    for sensor in temperature_info:
        if sensor.SensorType == u'Temperature' and sensor.Name == u'GPU Core':
            gpu_sensor = sensor
            return gpu_sensor.Value


def get_cpu_temp_max():
    temperature_info = w.Sensor()
    temp = 0
    for sensor in temperature_info:
        if sensor.SensorType == u'Temperature' and 'CPU' in sensor.Name:
            if sensor.Value > temp:
                temp = sensor.Value

    return temp


def get_cpu_load():
    sensor_info = w.Sensor()
    load = 0
    count = 0
    for sensor in sensor_info:
        if sensor.SensorType == u'Load' and 'CPU Core' in sensor.Name:
            load += sensor.Value
            count = count + 1

    return load / count

def get_cpu_temp_max_history():
    temperature_info = w.Sensor()
    temp = 0
    for sensor in temperature_info:
        if sensor.SensorType == u'Temperature' and 'CPU' in sensor.Name:
            if sensor.Max > temp:
                temp = sensor.Max

    return temp


def get_gpu_temp_max():
    temperature_info = w.Sensor()
    temp = 0
    for sensor in temperature_info:
        if sensor.SensorType == u'Temperature' and 'GPU' in sensor.Name:
            if sensor.Value > temp:
                temp = sensor.Value

    return temp



def get_gpu_temp_max_historic():
    temperature_info = w.Sensor()
    temp = 0
    for sensor in temperature_info:
        if sensor.SensorType == u'Temperature' and 'GPU' in sensor.Name:
            if sensor.Max > temp:
                temp = sensor.Max

    return temp

def get_gpu_load():
    sensor_info = w.Sensor()
    load = 0
    count = 0
    for sensor in sensor_info:
        if sensor.SensorType == u'Load' and 'GPU Core' in sensor.Name:
            load += sensor.Value
            count = count + 1

    if (count == 0):
        return -1
    else:
        return load / count


def generate_json(process_list):
    data = {}

    data['CPUTemp'] = int(get_cpu_temp_max())
    data['CPUMax'] = int(get_cpu_temp_max_history())
    data['CPULoad'] = int(get_cpu_load())
    data['GPUTemp'] = int(get_gpu_temp_max())
    data['GPUMax'] = int(get_gpu_temp_max_historic())
    data['GPULoad'] = int(get_gpu_load())
    data['IP'] = socket.gethostbyname(socket.gethostname())
    data['Name'] = os.environ['COMPUTERNAME']
    # data['Name'] = 'FARM1'
    data['Updated'] = time.time() * 1000

    get_cpu_load()

    for item in process_list:
        for process_name in item:
            process_exe = item[process_name]

            running = ProcessManager.process_running(process_exe)
            data[process_name] = running

    json_data = json.dumps(data)
    # print json_data
    return json_data
