import fnmatch
import os
import json
import glob
import time

import JobInfo
import sys
import Config

data = []
new_data = []
updated_at = 0

def getjobs():
    all_jobs = []

    playout_jobs = find_children(Config.BASE_DIR, 'AnimationRecordingInput', '*.json.job')

    for playout in playout_jobs:

        total = 0
        inprogress = 0
        done = 0

        clip_job = 0
        clip_job = find_child(Config.BASE_DIR, 'AnimationRecordingOutput', playout._name + '.clip.job')
        if not clip_job == 0:
            playout.add_job(clip_job)
            total += 1

        subclip_jobs = 0
        subclip_jobs = find_children(Config.BASE_DIR, 'SplitRenderingOutput', playout._name + '*.json.job')

        try:
            if not subclip_jobs == 0 and not clip_job == 0:
                clip_job.add_jobs(subclip_jobs)
                total += 1
        except:
            print "Unexpected error:", sys.exc_info()[0]

        count = -100
        render_folder = os.path.join('RenderingOutput/' + playout._name)
        render_jobs = find_children(Config.BASE_DIR, render_folder, '*.rs.job')
        render_composits = find_pngs(playout)

        playout._ispreview = True

        if(len(render_jobs)<=0):
            playout_render_folder = os.path.join(Config.BASE_DIR, render_folder);
            render_jobs = find_children(playout_render_folder, "", '*.job')
            playout._ispreview = False

        for render_job in render_jobs:

            if (playout._ispreview):
                dir_list = render_job._filename.split("/")
                frame = dir_list[-2]
                render_job._frame = int(frame)
                render_job._name = frame
                render_job._previewoption="Preview"
            else:
                dir_list = render_job._filename.split("/")
                frame = dir_list[-1]
                frame = frame[0:-4]
                render_job._frame = int(frame)
                render_job._name = frame
                find_missing_splitaction_pngs(render_job, playout)

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


def find_child(BASE_DIR, subdir, lookfor):
    search_dir = os.path.join(BASE_DIR, subdir)
    for root, dirnames, filenames in os.walk(search_dir):
        if lookfor.lower() in [x.lower() for x in filenames]:
            file = os.path.join(root, lookfor)
            job = JobInfo.JobInfo()
            job.create_from_file(file)
            return job
    return 0


def find_children(BASE_DIR, subdir, lookfor):
    list = []
    search_dir = os.path.join(BASE_DIR, subdir)
    for root, dirnames, filenames in os.walk(search_dir):
        for filename in fnmatch.filter(filenames, lookfor):
            file = os.path.join(root, filename)
            job = JobInfo.JobInfo()
            job.create_from_file(file)

            if subdir == 'SplitRenderingOutput':
                temppath = os.path.join(root, filename[:-4])
                filepath = temppath.replace("\\", "/")
                jsondata = json.load(open(filepath))
                job._framerange = str(jsondata['_from_frame']) + " - " + str(jsondata['_to_frame'])

            list.append(job)
    return list

# Gets all available pngs from "/CompositingOutput
def find_pngs(playout):
    list = []
    composite_folder = os.path.join('CompositingOutput/' + playout._name)
    path_string = os.path.join(Config.BASE_DIR, composite_folder)

    if os.path.isdir(path_string):
        os.chdir(path_string)
        list = glob.glob('*.png')

    return list

# Checks if any pngs are missing for each frame
def find_missing_splitaction_pngs(renderjob, playout):

    if len(str(renderjob._name)) < 4:
        padded_frame = renderjob._name.zfill(4) + ".png"

    composite_folder = os.path.join(Config.BASE_DIR, 'CompositingOutput/' + playout._name)

    if os.path.isdir(composite_folder):

        expected_elements = ["Light", "Main", "Map", "Stencil", "UV"]
        missing_elements = []
        renderjob._missing = False

        for element in expected_elements:
            element_path = os.path.join(composite_folder, element + "." + padded_frame)
            if not os.path.exists(element_path):
                renderjob._missing = True
                missing_elements.append(element)

        if renderjob._missing:
            renderjob._missingstring =" | ".join(missing_elements)
        else:
            renderjob._missingstring = "All Files"

def update():
    global data
    data = getjobs()

    global updated_at
    updated_at = time.strftime("%d/%m/%y %H:%M:%S")




