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
playout_job_framerange = {'Lowest': -1, 'Highest': -1}

status_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}
current_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}
log_text = ""

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

            # Getting list of all expected frame numbers to compare for missing frames
            expected_frames = []
            for x in range(playout_job_framerange['Lowest'], playout_job_framerange['Highest'] + 1):
                expected_frames.append(x)

        # First look for production renders
        render_folder = os.path.join('RenderingOutput/' + playout_job._name)
        production_render_folder = os.path.join(Config.BASE_DIR, render_folder);
        render_jobs = find_children(production_render_folder, "", '*.job', False)
        playout_job._ispreview = False

        if not render_jobs:
            # No production render, check for preview renders
            render_jobs = find_children(Config.BASE_DIR, render_folder, '*.rs.job')
            playout_job._ispreview = True

        # All render job frames are added to an available list to compare with expected frames
        available_frames = []
        # Count keeping track of frame numbers
        # Count iterates for available frames, and for each missing frame to display correct missing number
        count = 0
        for render_job in render_jobs:

            # Adding additional render_job information
            if (playout_job._ispreview):
                dir_list = render_job._filename.split("/")
                frame = dir_list[-2]
                render_job._previewoption = "Preview"
            else:
                dir_list = render_job._filename.split("/")
                frame = dir_list[-1]
                frame = frame[0:-4]
                find_missing_splitaction_pngs(render_job, playout_job)

            render_job._frame = int(frame)
            render_job._name = frame

            # Detecting any missing frames before the current render_job frame
            available_frames.append(render_job._frame)
            if render_job._frame != expected_frames[count]:
                count = find_missing_frames(render_job, count, playout_job, expected_frames[count])
                # delete element in expected frames to compare next render_job frame to correct index of expected frames
                del expected_frames[count]
                playout_job.add_job(render_job)
            else:
                playout_job.add_job(render_job)
                count += 1

            # Special case for last element in index to detect for missing frames ahead of current render_job frame
            if render_job == render_jobs[len(render_jobs)-1]:
                if render_job._frame != expected_frames[len(expected_frames)-1]:
                    find_missing_frames(render_job, count, playout_job, expected_frames[len(expected_frames) - 1], True)

        # Resetting frame ranges for new playout ranges
        playout_job_framerange['Lowest'] = -1
        playout_job_framerange['Highest'] = -1

        all_jobs.append(playout_job)

    return all_jobs

def find_missing_frames(render_job, count, playout_job, expected_frame, last_index=False):

    missing_frames_count = abs(render_job._frame - expected_frame)

    for x in range(missing_frames_count):
        temp_job = JobInfo.JobInfo()

        if last_index:
            temp_job._name = "MISSING " + str(render_job._frame + x + 1)
        else:
            temp_job._name = "MISSING " + str(render_job._frame - missing_frames_count + x)

        temp_job._frame = count  # int(frame)
        temp_job._status = "MISSING"
        temp_job._agent = "N/A"
        playout_job.add_job(temp_job)
        count += 1

    return count

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
                global playout_job_framerange

                temppath = entry.path[:-4]
                filepath = temppath.replace("\\", "/")
                jsondata = json.load(open(filepath))
                job._framerange = str(jsondata['_from_frame']) + " - " + str(jsondata['_to_frame'])

                lowest_frame = (jsondata['_from_frame'])
                highest_frame = (jsondata['_to_frame'])

                if playout_job_framerange['Lowest'] < 0 or playout_job_framerange['Highest'] < 0:
                    playout_job_framerange['Lowest'] = lowest_frame
                    playout_job_framerange['Highest'] = highest_frame

                if playout_job_framerange['Lowest'] > lowest_frame:
                    playout_job_framerange['Lowest'] = lowest_frame

                if playout_job_framerange['Highest'] < highest_frame:
                    playout_job_framerange['Highest'] = highest_frame

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
    global log_text

    with open('C:/Users/shadow/Desktop/Test/rpm_log.txt', 'r') as myfile:
        log_text = myfile.readlines()

    data = getjobs()
    updated_at = time.strftime("%d/%m/%y %H:%M:%S")

    current_total_summary = status_total_summary

    status_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}
