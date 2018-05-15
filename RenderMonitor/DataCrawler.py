import fnmatch
import os
import json
import time
import datetime

import JobInfo
import Config

try:
    from os import scandir
except ImportError:
    from scandir import scandir

data = []
new_data = []
updated_at = 0

all_rendered_frames = 0
queued_render_frames = 0
all_missing_frames = 0
all_done_renders_max_time = 0
all_done_subclips_max_time = 0
queued_subclips = 0
done_subclips = 0

working_rs_farms = []
working_subclip_farms = []

average_render_time = ""
remaining_render_time = ""

subclips_busy = True

frames_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}
current_frame_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}

playouts_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0}
current_playouts_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0}

playout_job_framerange = {'Lowest': -1, 'Highest': -1}

def get_jobs():
    global average_render_time
    all_jobs = []
    playout_jobs = find_children(Config.BASE_DIR, 'AnimationRecordingInput', '*.json.job')

    for playout_job in playout_jobs:

        find_vv_jobs(playout_job)

        expected_frames = []
        # expected frames remains empty if there are no clip jobs
        find_clip_jobs(playout_job, expected_frames)

        find_render_jobs(playout_job, expected_frames)

        if not playout_job._ispreview:
            formatted_average_time = str(datetime.timedelta(seconds=all_done_renders_max_time / all_rendered_frames)).split(":")
            average_render_time = formatted_average_time[1] + "m " + formatted_average_time[2] + 's'

        # Setting summary for subclips
        if subclips_busy == False:
            playout_job._subclips_summary = "Busy"
        else:
            playout_job._subclips_summary = "Done"

        # checking video output state
        find_video_outputs(playout_job)

        # Resetting values for new playout
        global subclips_busy
        subclips_busy = True

        playout_job_framerange['Lowest'] = -1
        playout_job_framerange['Highest'] = -1

        all_jobs.append(playout_job)

    return all_jobs

def find_vv_jobs(playout_job):

    vv_job_path = os.path.join(Config.BASE_DIR, 'VideoEncodingInput')
    vv_job_path = os.path.join(vv_job_path, playout_job._name + '.json.job')

    if os.path.isfile(vv_job_path):
        vv_job = JobInfo.JobInfo()
        vv_job.create_from_file(vv_job_path)
        playout_job.add_job(vv_job)

def find_video_outputs(playout_job):

    playout_job._video_output = "Not Started"

    video_output_path = os.path.join(Config.BASE_DIR, "VideoOutput")
    folder_content = list(scandir(video_output_path))
    playout_name = playout_job._name.lower()

    for x in folder_content:
        if playout_name in x.name.lower():
            playout_job._video_output = "Done"

def find_clip_jobs(playout_job, expected_frames):

    clip_job_path = os.path.join(Config.BASE_DIR, 'AnimationRecordingOutput')
    clip_job_path = os.path.join(clip_job_path, playout_job._name + '.clip.job')

    if os.path.isfile(clip_job_path):

        clip_job = JobInfo.JobInfo()
        clip_job.create_from_file(clip_job_path)
        playout_job.add_job(clip_job)

        subclip_jobs = find_children(Config.BASE_DIR, 'SplitRenderingOutput', playout_job._name + '*.json.job')
        clip_job.add_jobs(subclip_jobs)

        add_to_status_total("", clip_job_path)

        # Getting list of all expected frame numbers to compare for missing frames
        for x in range(playout_job_framerange['Lowest'], playout_job_framerange['Highest'] + 1):
            expected_frames.append(x)

def find_render_jobs(playout_job, expected_frames):

    # First look for production renders
    render_folder = os.path.join('RenderingOutput/' + playout_job._name)

    playout_job._ispreview = False
    render_jobs = find_children(Config.BASE_DIR, render_folder, '*.job', False)

    playout_job._rs_exports_summary = 0
    rs_count = 0
    no_frames = (playout_job_framerange['Highest'] - playout_job_framerange['Lowest']) + 1
    production_render_folder = os.path.join(Config.BASE_DIR, render_folder)
    if not render_jobs:
        # No production render, check for preview renders
        playout_job._ispreview = True
        render_jobs = find_children(Config.BASE_DIR, render_folder, '*.rs.job', True, playout_job, 3)

        for item in scandir(production_render_folder):
            if item.is_dir(follow_symlinks=False):
                folder_content = scandir(item.path)
                if [file for file in folder_content if file.name.endswith('.rs', 0)]:
                    rs_count += 1

        playout_job._rs_exports_summary = int((rs_count / float(no_frames)) * 100)

    else:
        for item in scandir(production_render_folder):
            if item.is_dir(follow_symlinks=False):
                folder_content = os.listdir(item.path)
                if len(list(folder_content)) == 3:
                    rs_count += 1

        playout_job._rs_exports_summary = int((rs_count / float(no_frames)) * 100)

    # All render job frames are added to an available list to compare with expected frames
    available_frames = []
    # render_count iterates for available frames, and for each missing frame to display correct missing number
    render_count = 0
    # Counting all pngs and comparing amount to expected amount
    missing_png_count = 0
    # Counting all done frames and max rendered time to get average render time
    rendered_jobs = 0
    current_rendered_time = 0
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
            # find any missing pngs for composite renders
            missing_png_count += find_missing_pngs(render_job, playout_job)

        render_job._frame = int(frame)
        render_job._name = frame

        # Detecting any missing frames before the current render_job frame
        available_frames.append(render_job._frame)
        if render_job._frame != expected_frames[render_count]:
            render_count = find_missing_frames(render_job, render_count, playout_job, expected_frames[render_count])
            # delete element in expected frames to compare next render_job frame to correct index of expected frames
            del expected_frames[render_count]
            playout_job.add_job(render_job)
        else:
            playout_job.add_job(render_job)
            render_count += 1

        # Special case for last element in index to detect for missing frames ahead of current render_job frame
        if render_job == render_jobs[len(render_jobs) - 1]:
            if render_job._frame != expected_frames[len(expected_frames) - 1]:
                find_missing_frames(render_job, render_count, playout_job, expected_frames[len(expected_frames) - 1], True)

        if not playout_job._ispreview:
            if render_job._status == 'Done':
                rendered_jobs += 1
                split_time = render_job._time.split(':')
                render_time = (int(split_time[1]) * 60) + int(split_time[2])
                current_rendered_time = current_rendered_time + render_time
            elif render_job._status =='Busy':
                if not render_job._agent in working_rs_farms:
                    global working_rs_farms
                    working_rs_farms.append(str(render_job._agent))

    playout_job._renders_summary = 0
    if (playout_job._ispreview):
        preview_renders_subdir = os.path.join('PreviewFrameRenderingOutput', playout_job._name)
        preview_renders_path = os.path.join(Config.BASE_DIR, preview_renders_subdir)
        folder_content = scandir(preview_renders_path)
        folder_content_length = len(list(folder_content))
        playout_job._renders_summary = int((folder_content_length / float(no_frames)) * 100)
    else:
        global all_rendered_frames
        global all_done_renders_max_time
        global queued_render_frames

        no_pngs = no_frames * 5
        available_pngs = no_pngs - missing_png_count
        playout_job._renders_summary = int((available_pngs / float(no_pngs)) * 100)

        all_done_renders_max_time = all_done_renders_max_time + current_rendered_time
        all_rendered_frames = all_rendered_frames + rendered_jobs
        queued_render_frames = queued_render_frames + abs(no_frames-rendered_jobs)

def find_child(base_dir, subdir, lookfor):
    search_dir = os.path.join(base_dir, subdir)
    for root, dirnames, filenames in os.walk(search_dir):
        if lookfor.lower() in [x.lower() for x in filenames]:
            file = os.path.join(root, lookfor)
            job = JobInfo.JobInfo()
            job.create_from_file(file)
            add_to_status_total(root, lookfor)
            return job
    return 0

def find_children(base_dir, subdir, lookfor, recursive=True, playout_job = None, rs_count=0):
    jobs = []
    search_dir = os.path.join(base_dir, subdir)

    # Sometimes RenderingOutPut takes a few minutes to generate all folders
    # This checks if the folder exists yet
    # A similiar fix needs to be applied in find_render_jobs, can't fix at the moment because redshift1
    # - just generated the missing folder as I was fixing the issue
    if os.path.isdir(search_dir):
        for entry in scandir(search_dir):
            if entry.is_dir(follow_symlinks=False):
                if (recursive):
                    if playout_job == None:
                        jobs += find_children(base_dir, subdir + "\\" + entry.name, lookfor)
                    else:
                        jobs += find_children(base_dir, subdir + "\\" + entry.name, lookfor, True, playout_job)

            elif fnmatch.fnmatch(entry.name, lookfor):
                job = JobInfo.JobInfo()
                job.create_from_file(entry.path)
                jobs.append(job)
                add_to_status_total("", entry.path)

                # Get method for checking frames and subclip busy summary
                calculate_subclip_summary(subdir, entry, job)


    return jobs

def calculate_subclip_summary(subdir, entry, job):
    if "SplitRenderingOutput" in subdir:
        global playout_job_framerange
        global subclips_busy

        json_path = entry.path[:-4]
        filepath = json_path.replace("\\", "/")
        jsondata_json = json.load(open(filepath))
        job._framerange = str(jsondata_json['_from_frame']) + " - " + str(jsondata_json['_to_frame'])

        lowest_frame = (jsondata_json['_from_frame'])
        highest_frame = (jsondata_json['_to_frame'])

        if playout_job_framerange['Lowest'] < 0 or playout_job_framerange['Highest'] < 0:
            playout_job_framerange['Lowest'] = lowest_frame
            playout_job_framerange['Highest'] = highest_frame

        if playout_job_framerange['Lowest'] > lowest_frame:
            playout_job_framerange['Lowest'] = lowest_frame

        if playout_job_framerange['Highest'] < highest_frame:
            playout_job_framerange['Highest'] = highest_frame

        job_path = entry.path
        filepath = job_path.replace("\\", "/")
        jsondata_job = json.load(open(filepath))

        clipjob_status = (jsondata_job['_job_state'])

        # Checking if all subclips are done
        # Get an error value too. Make the count -1 for an error
        if clipjob_status != 2:
            global queued_subclips

            queued_subclips += 1
            subclips_busy = False
            if clipjob_status == 1:
                if not job._agent in working_subclip_farms:
                    working_subclip_farms.append(str(job._agent))
        else:
            global all_done_subclips_max_time
            global done_subclips

            done_subclips += 1
            split_time = job._time.split(':')
            subclip_time = (int(split_time[1]) * 60) + int(split_time[2])

            all_done_subclips_max_time = all_done_subclips_max_time + subclip_time


def find_missing_frames(render_job, render_count, playout_job, expected_frame, last_index=False):

    missing_frames_count = abs(render_job._frame - expected_frame)
    global all_rendered_frames
    global all_missing_frames

    for x in range(missing_frames_count):
        temp_job = JobInfo.JobInfo()

        if last_index:
            temp_job._name = "MISSING " + str(render_job._frame + x + 1)
        else:
            temp_job._name = "MISSING " + str(render_job._frame - missing_frames_count + x)

        temp_job._frame = render_count
        temp_job._status = "Missing"
        temp_job._agent = "N/A"
        playout_job.add_job(temp_job)
        render_count += 1

        all_rendered_frames +=1
        all_missing_frames +=1

    return render_count

def add_to_status_total(BASE_DIR, subdir):
    file = os.path.join(BASE_DIR, subdir)

    file_Path = file.replace("\\", "/")
    json_Data = json.load(open(file_Path))
    job_State = json_Data['_job_state']

    switch_Dictionary = {0: 'Queued', 1: 'Busy', 2: 'Done', 3: 'Error'}

    # Condition for playouts' statuses
    if "AnimationRecordingInput" in file:
        playouts_total_summary[switch_Dictionary[job_State]] += 1
    else:
        frames_total_summary[switch_Dictionary[job_State]] += 1

# Checks if any pngs are missing for each frame
def find_missing_pngs(renderjob, playout):
    
    padded_frame = renderjob._name.zfill(4) + ".png"
    composite_folder = os.path.join(Config.BASE_DIR, 'CompositingOutput/' + playout._name)

    missing_png_count = 0

    if os.path.isdir(composite_folder):

        expected_elements = ["Light", "Main", "Map", "Stencil", "UV"]
        missing_elements = []
        renderjob._missing = False

        for element in expected_elements:
            element_path = os.path.join(composite_folder, element + "." + padded_frame)
            if not os.path.exists(element_path):
                renderjob._missing = True
                missing_elements.append(element)
                missing_png_count += 1

        if renderjob._missing:
            renderjob._missingstring =" | ".join(missing_elements)
        else:
            renderjob._missingstring = "All Files"

        return missing_png_count

    return 0

def calculate_remaining_time():
    global remaining_render_time

    global queued_render_frames
    global all_done_renders_max_time
    global all_rendered_frames

    global queued_subclips
    global all_done_subclips_max_time
    global done_subclips

    # All render jobs that aren't busy rendering will show up as missing, therefore all missing frames
    # -and the 1 busy frame job will be used to find the remaining amount of frames to render (queued)
    if len(working_rs_farms) == 0:
        parallel_farm_rs_time = ((queued_render_frames) * (all_done_renders_max_time / all_rendered_frames)) / 1
    else:
        parallel_farm_rs_time = ((queued_render_frames)*(all_done_renders_max_time / all_rendered_frames))/len(working_rs_farms)

    formatted_rs_time = str(datetime.timedelta(seconds=parallel_farm_rs_time)).split(":")

    if len(working_subclip_farms) == 0:
        parallel_farm_subclip_time = (queued_subclips) * (all_done_subclips_max_time / done_subclips)
    else:
        parallel_farm_subclip_time = ((queued_subclips) * (all_done_subclips_max_time / done_subclips))/len(working_subclip_farms)

    formatted_subclip_time = str(datetime.timedelta(seconds=parallel_farm_subclip_time)).split(":")

    if formatted_subclip_time > formatted_rs_time:
        remaining_render_time = formatted_subclip_time[0] + "hr " + formatted_subclip_time[1] + "m"
    else:
        remaining_render_time = formatted_rs_time[0] + "hr " + formatted_rs_time[1] + "m"

    queued_render_frames = 0
    all_done_renders_max_time = 0
    all_rendered_frames = 0

    queued_subclips = 0
    all_done_subclips_max_time = 0
    done_subclips = 0


    # revert if total time left not working
    # formatted_render_time = str(datetime.timedelta(seconds=(queued_render_frames) * (all_done_renders_max_time / all_rendered_frames))).split(":")
    # parallel_farm_render_time = (formatted_render_Time/no_farms)

def update():
    global data
    global current_frame_total_summary
    global frames_total_summary
    global current_playouts_total_summary
    global playouts_total_summary
    global updated_at
    global log_text

    with open('//luma-redshift1/e$/RPM/RPM/rpm_log.txt', 'r') as myfile:
        log_text = myfile.readlines()


    data = get_jobs()
    updated_at = time.strftime("%d/%m/%y %H:%M:%S")

    current_frame_total_summary = frames_total_summary
    current_playouts_total_summary = playouts_total_summary

    calculate_remaining_time()


    frames_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0, 'Error': 0}
    playouts_total_summary = {'Queued': 0, 'Busy': 0, 'Done': 0}

