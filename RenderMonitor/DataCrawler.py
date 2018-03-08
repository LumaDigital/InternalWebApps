import fnmatch
import os
import json

import time

import JobInfo
import sys

basedir = "Z:\\"
data = []
new_data = []
updated_at = 0

def getjobs():
    all_jobs = []

    playout_jobs = find_children(basedir, 'AnimationRecordingInput', '*.json.job')

    for playout in playout_jobs:

        total = 0
        inprogress = 0
        done = 0

        clip_job = 0
        clip_job = find_child(basedir, 'AnimationRecordingOutput', playout._name + '.clip.job')
        if not clip_job == 0:
            playout.add_job(clip_job)
            total += 1

        subclip_jobs = 0
        subclip_jobs = find_children(basedir, 'SplitRenderingOutput', playout._name + '*.json.job')

        try:
            if not subclip_jobs == 0 and not clip_job == 0:
                clip_job.add_jobs(subclip_jobs)
                total += 1
        except:
            print "Unexpected error:", sys.exc_info()[0]

        render_folder = os.path.join('RenderingOutput/' + playout._name)
        render_jobs = find_children(basedir, render_folder, '*.rs.job')
        count = -100

        for render_job in render_jobs:
            frame = render_job._filename.split("/")
            frame = frame[-2]
            render_job._name = "RS Frame " + frame
            render_job._frame = int(frame)

            if (count < 0):
                count = render_job._frame

            while(not count == int(frame)):
               tempJob=JobInfo.JobInfo()
               tempJob._name = "MISSING " + str(count)
               tempJob._frame = count #int(frame)
               tempJob._status = "MISSING"
               tempJob._agent = "N/A"
               playout.add_job(tempJob)
               count += 1

               if count == int(frame):
                   break

            playout.add_job(render_job)
            total += 1
            count += 1

        all_jobs.append(playout)

    return all_jobs


def find_child(basedir, subdir, lookfor):
    search_dir = os.path.join(basedir, subdir)
    for root, dirnames, filenames in os.walk(search_dir):
        if (lookfor) in filenames:
            file = os.path.join(root, lookfor)
            job = JobInfo.JobInfo()
            job.create_from_file(file)
            return job
    return 0


def find_children(basedir, subdir, lookfor):
    list = []
    search_dir = os.path.join(basedir, subdir)
    for root, dirnames, filenames in os.walk(search_dir):
        for filename in fnmatch.filter(filenames, lookfor):
            file = os.path.join(root, filename)
            job = JobInfo.JobInfo()
            job.create_from_file(file)
            list.append(job)
    return list


def update():
    # global data
    # data = find_atomic_jobs()

    global data
    data = getjobs()

    global updated_at
    updated_at = time.strftime("%d/%m/%y %H:%M:%S")
    # print data


