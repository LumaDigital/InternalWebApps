import fnmatch
import os
import json
import time

import JobInfo
import Config

try:
    from os import scandir
except ImportError:
    from scandir import scandir

data = []
new_data = []
updated_at = 0

status_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}
current_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}

def getjobs():
    all_jobs = []

    playout_jobs = find_children(Config.BASE_DIR, 'AnimationRecordingInput', '*.json.job')

    for playout_job in playout_jobs:

        clip_job_path = os.path.join(Config.BASE_DIR, 'AnimationRecordingOutput')
        clip_job_path = os.path.join(clip_job_path, playout_job._name + '.clip.job')
        if os.path.isfile(clip_job_path):
            clip_job = JobInfo.JobInfo()
            clip_job.create_from_file(clip_job_path)
            playout_job.add_job(clip_job)

            subclip_jobs = find_children(Config.BASE_DIR, 'SplitRenderingOutput', playout_job._name + '*.json.job')
            clip_job.add_jobs(subclip_jobs)

            AddToStatusTotal("", clip_job_path)

        # For counting frames? Why hardcoded -100?
        count = -100

        # First look for production renders
        render_folder = os.path.join('RenderingOutput/' + playout_job._name)
        production_render_folder = os.path.join(Config.BASE_DIR, render_folder);
        render_jobs = find_children(production_render_folder, "", '*.job', False)
        playout_job._ispreview = False

        if not render_jobs:
            # No production render, check for preview renders
            render_jobs = find_children(Config.BASE_DIR, render_folder, '*.rs.job')
            playout_job._ispreview = True

        for render_job in render_jobs:

            if (playout_job._ispreview):
                dir_list = render_job._filename.split("/")
                frame = dir_list[-2]
                render_job._previewoption="Preview"
            else:
                dir_list = render_job._filename.split("/")
                frame = dir_list[-1]
                frame = frame[0:-4]
                find_missing_splitaction_pngs(render_job, playout_job)

            render_job._frame = int(frame)
            render_job._name = frame

            if (count < 0):
                count = render_job._frame

            while (not count == int(frame)):
               tempJob=JobInfo.JobInfo()
               tempJob._name = "MISSING " + str(count)
               tempJob._frame = count #int(frame)
               tempJob._status = "MISSING"
               tempJob._agent = "N/A"
               playout_job.add_job(tempJob)
               count += 1

            playout_job.add_job(render_job)
            count += 1

        all_jobs.append(playout_job)

    return all_jobs

def AddToStatusTotal(BASE_DIR, subdir):
    file = os.path.join(BASE_DIR, subdir)

    file_Path = file.replace("\\", "/")
    json_Data = json.load(open(file_Path))
    job_State = json_Data['_job_state']

    switch_Dictionary = {0: 'Queued', 1: 'Busy', 2: 'Done', 3: 'Error'}

    status_total_summary[switch_Dictionary[job_State]] += 1



def find_child(BASE_DIR, subdir, lookfor):
    search_dir = os.path.join(BASE_DIR, subdir)
    for root, dirnames, filenames in os.walk(search_dir):
        if lookfor.lower() in [x.lower() for x in filenames]:
            file = os.path.join(root, lookfor)
            job = JobInfo.JobInfo()
            job.create_from_file(file)
            AddToStatusTotal(root, lookfor)
            return job
    return 0

def find_children(BASE_DIR, subdir, lookfor, recursive=True):
    jobs = []
    search_dir = os.path.join(BASE_DIR, subdir)

    for entry in scandir(search_dir):
        if entry.is_dir(follow_symlinks=False):
            if (recursive):
                jobs += find_children(BASE_DIR, subdir +"\\"+ entry.name, lookfor)

        elif fnmatch.fnmatch(entry.name, lookfor):
            job = JobInfo.JobInfo()
            job.create_from_file(entry.path)
            jobs.append(job)
            AddToStatusTotal("", entry.path)

            if "SplitRenderingOutput" in subdir:
                temppath = entry.path[:-4]
                filepath = temppath.replace("\\", "/")
                jsondata = json.load(open(filepath))
                job._framerange = str(jsondata['_from_frame']) + " - " + str(jsondata['_to_frame'])

    return jobs

# Checks if any pngs are missing for each frame
def find_missing_splitaction_pngs(renderjob, playout):

    # TODO if this fails padded_frame is unset
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
    global current_total_summary
    global status_total_summary
    global updated_at

    data = getjobs()
    updated_at = time.strftime("%d/%m/%y %H:%M:%S")

    current_total_summary = status_total_summary

    status_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}




