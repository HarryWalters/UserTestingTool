
import cv2 # I am running version 4.7.0
import argparse # This takes in any command-line arguments that the users enters.
import os # This allows us to check other directories, if we need to.
from tqdm import tqdm # This makes the pretty loading bars that you see
import csv # to write the timings to a csv file.
import gc # just in case there's any memory leaks (opencv can be weird)

"""
Video to Metrics Converter
Convert your Usability Test screen recordings into insightful metrics.

Usage: python3 videoToMetricsConverter.py <path/to/app_screenshots> <path/to/screen_recordings>

Args:
    app_screens_directory (str): Path to the App Screens Directory.
    video_recording (str/list): Path to the Video Recording.
        If you provide a directory, it will process every video in the directory.
        If you provide a file (or list of files), it will process the file(s) listed.
    output_data_directory (str): The name of the folder where we'll save our generated metrics. Default = 'generated_metrics'
    sample_rate (int): The number of times we analyze the video (per second). Default = 2.
    resize_factor (float): The percentage of the original images that we shrink by for analysis. Default = 0.25.
    feature_cutoff (int): If any frames are poorly detected (fewer features than the cutoff), we'll ignore them. Default = 10.
    additional_image_types (str/list): If your image screenshots are of an unconventional filetype, enter the filetype(s) here. Default = "".
    additional_video_types (str/list): If your video screenshots are of an unconventional filetype, enter the filetype(s) here. Default = "".
    header (bool): Specifies whether to write an initial row of header data to the output file(s). Default = True.
    verbose (bool): Enable verbose output. Default = True.

Returns:
    None
"""


def detect_page(frame, full_descriptors):
    _, full_frame_desc = orb.detectAndCompute(frame, None)
    full_frame_scores = []
    for page in full_descriptors.keys():
            full_matches = bf_match.match(full_descriptors[page], full_frame_desc)
            full_frame_scores.append([page, len(full_matches)])

    full_frame_scores = sorted(full_frame_scores, key = lambda x: x[1])[::-1]
    # clear memory
    full_frame_desc = None
    return full_frame_scores[0]

def string_or_list(arg_value):
    #If it's a single file, or a single directory name, keep it as is.
    output = arg_value
    if "," in arg_value:
        output = arg_value.split(",")
        # if the first character of the first file has [,
        if output[0][0] == "[":
            # get rid of it
            output[0] = output[0][1:]
        # if the last character of the last file has ],
        if output[len(output)-1][-1] == "]":
            # get rid of it.
            output[len(output)-1] = output[len(output)-1][:-1]
    return output

def getFileNames(directory, extensions):
    return [os.path.join(directory,f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and os.path.splitext(f)[1].lower() in extensions]

parser = argparse.ArgumentParser(
    description="Video to Metrics Converter\n"
                "Convert your Usability Test screen recordings into insightful metrics.",
    formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument(
    "app_screens_directory",
    type=str, 
    help="Path to the App Screens Directory.")
    
parser.add_argument(
    "video_recording",
    type=string_or_list,
    help="Path to the Video Recording.\n"
         "If you provide a directory, it will process every video in the directory.\n"
         "If you provide a file (or list of files), it will process the file(s) listed.")

parser.add_argument(
    "--output_data_directory",
    type=str,
    default="generated_metrics",
    help="The name of the folder where we'll save our generated metrics. Default = 'generated_metrics'")
    
parser.add_argument(
    "--sample_rate",
    type=int,
    default=2,
    help="The number of times we analyse the video (per second). Default = 2")

parser.add_argument(
    "--resize_factor",
    type=float,
    default=0.25,
    help="The percentage of the original images that we shrink by, for analysis. Default = 0.25")

parser.add_argument(
    "--feature_cutoff",
    type=int,
    default=10,
    help="If any frames are poorly detected (fewer features than the cutoff), we'll ignore them. Default = 10")

parser.add_argument(
    "--additional_image_types",
    type=string_or_list,
    default="",
    help='If your image screenshots are of an unconventional filetype, enter the filetype(s) here. Default = ""')

parser.add_argument(
    "--additional_video_types",
    type=string_or_list,
    default="",
    help='If your video screenshots are of an unconventional filetype, enter the filetype(s) here. Default = ""')

parser.add_argument(
    "--header",
    type=bool,
    default=True,
    help="Specifies whether to write an initial row of header data to the output file(s). Default = True")
    
parser.add_argument(
    '-v', '--verbose', 
    #action='store_true',
    default=True,
    help='Enable verbose output.')
    
args = parser.parse_args()
#input(args.app_screens_directory)
gc.collect() # If you close the code early, 
             # this makes sure that we've got enough memory to work with.

image_extensions = [".jpg", ".jpeg", ".png",".raw"]
video_extensions = [".mp4", ".mov", ".avi"]


### ADDITIONAL FILETYPES ###
# if the user specifies multiple unique filetypes
if type(args.additional_image_types) == list:
    # for any of the filetypes that the user has added,
    for image_type in args.additional_image_types:
        # if the user has just written "jpg", and not ".jpg",
        if image_type[0] != ".":
            # add that "." at the beginning of the extention.
            temp_image_type = "." + image_type.lower()
        else:
            temp_image_type = image_type.lower()
        # if we haven't seen this type before,
        if temp_image_type not in image_extensions:
            # add it to the list
            image_extensions.append(temp_image_type)
# else, if user has just provided 1 new extension.
elif len(args.additional_image_types) > 1:
    # if the user has just written "jpg", and not ".jpg",
    if args.additional_image_types[0] != ".":
        # add that "." at the beginning of the extention.
        temp_image_type = "." + args.additional_image_types.lower()
    else:
        temp_image_type = args.additional_image_types.lower()
    # if we haven't seen this type before,
    if temp_image_type not in image_extensions:
        # add it to the list
        image_extensions.append(temp_image_type)



if type(args.additional_video_types) == list:
    # for any of the filetypes that the user has added,
    for video_type in args.additional_video_types:
        # if the user has just written "jpg", and not ".jpg",
        if video_type[0] != ".":
            # add that "." at the beginning of the extention.
            temp_video_type = "." + video_type.lower()
        else:
            temp_video_type = video_type.lower()
        # if we haven't seen this type before,
        if temp_video_type not in video_extensions:
            # add it to the list
            video_extensions.append(temp_video_type)
            
# The user has just provided 1 new extension.
elif len(args.additional_video_types) > 1:
    # if the user has just written "jpg", and not ".jpg",
    if args.additional_video_types[0] != ".":
            # add that "." at the beginning of the extention.
            temp_video_type = "." + args.additional_video_types.lower()
    else:
        temp_video_type = args.additional_video_types.lower()
    # if we haven't seen this type before,
    if temp_video_type not in video_extensions:
        # add it to the list
        video_extensions.append(temp_video_type)
            
############################


### IF THE USER SPECIFIES ONE OR MORE VIDEOS ####

if type(args.video_recording) == list:
    video_names = args.video_recording
elif type(args.video_recording) == str:
    if args.video_recording[-4:].lower() in video_extensions:
        video_names = [args.video_recording]
    else:
        video_names = getFileNames(args.video_recording, video_extensions)
#################################################

image_names = getFileNames(args.app_screens_directory, image_extensions)

# The secret sauce. Our template matches uses scale-invariant feature transform
# to detect frames.
orb = cv2.SIFT_create()

images = []
full_descriptors = {}

bf_match = cv2.BFMatcher(cv2.NORM_L1, crossCheck=True)



if args.verbose:
    print("Loading in images and calculating features (Please Wait)")

pages = []

for image_path in tqdm(image_names, unit="images", 
                       bar_format="{l_bar}{bar}| {remaining} {rate_fmt} "):
    image_file = image_path.split("/")[-1].split("\\")[1]
    pages.append(image_file[:-4])
    # 2778, 1284 for iPhone 13 Pro Max
    temp_image = cv2.imread(image_path)
    # keypoints, descriptors (we only care about about the descriptors)
    tiny_image = cv2.resize(temp_image, (0,0), fx=args.resize_factor, 
                                               fy=args.resize_factor)
    _, full_descriptors[image_file] = orb.detectAndCompute(tiny_image, None)

if args.verbose:
    print("Loaded images.")

folder_name = args.output_data_directory.split("/")[-1].split("\\")[-1]
output_folder_path = os.path.join(os.getcwd(), folder_name)

if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)
# Template Matching interval
sampling_interval = 1000/args.sample_rate # 500 milliseconds, half a second.

for video_name in video_names:
    # This is our "play head". We haven't seen any frames of the video, 
    # so it's at 0.
    duration = 0
    # This will store which of the pages was seen, and when.
    timeline = []
    
    # if there's filepath information in the video_name,
    if len(video_name.split("/")[-1].split("\\")) > 1:
        # just extract the file component, for prettiness later on.
        video_title = video_name.split("/")[-1]
    else:
        video_title = video_name
        
    video = cv2.VideoCapture(video_name) # loading the video up.
    if args.verbose:
        print("Analysing " + video_title + "...")
        
    # used to make a pretty loading bar.
    total_frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT)) 

    current_time = 0
    current_frame = 0
    
    loading_bar = tqdm(total=total_frame_count, leave=True, unit="frames", 
                       bar_format="{l_bar}{bar}| {remaining} {rate_fmt} ")
    
    frame = 'the first frame'
    while current_frame < total_frame_count and frame is not None:
        ret, frame = video.read()
        
        # most videos don't have EXACT integer frame rates, so this finds the
        # closest next frame to analyse.
        current_time = video.get(cv2.CAP_PROP_POS_MSEC) 
            
        if frame is not None:
            tiny_frame = cv2.resize(frame, (0,0), fx=args.resize_factor,
                                                  fy=args.resize_factor)
            page_and_confidence = detect_page(tiny_frame, full_descriptors)
            
            # move our "play head", onto the next frame for analysis
            duration += sampling_interval
            
            video.set(cv2.CAP_PROP_POS_MSEC, duration)
            new_time = video.get(cv2.CAP_PROP_POS_MSEC)
            new_frame = video.get(cv2.CAP_PROP_POS_FRAMES)
            
            # clamp the loading bar between 0 and 1
            bar_chunk = max(new_frame-current_frame,0)
            loading_bar.update(bar_chunk)
            timeline.append([page_and_confidence, (current_time)/1000])
            current_frame = new_frame

    loading_bar.close()

    ### CLEANING UP THE TIMELINE ###
    # if there's any pages with fewer than (default=10) keypoints,
    # give their labels a "low confident detection"
    timeline = [page if page[0][1] > args.feature_cutoff else [["low confidence detection    ", 0],0] for page in timeline]
    
    # the first page that we detect in the video.
    timeline_cleaned = [[timeline[0][0][0], 0, 0]]
    cumulative = 0
    for i in range(len(timeline)):
        # if we have a low confidence detection, ignore it.
        if timeline[i][0][0] == "low confidence detection    ": 
            # apologies for the 'pass'. I know it's not the *best* to have them!
            pass
        
        # if the current page is different from the most recent one seen,
        elif timeline[i][0][0] != timeline_cleaned[-1][0]:
            timeline_cleaned[-1][2] = timeline[i][1] # cumulative 
            timeline_cleaned[-1][1] = timeline[i][1] - timeline_cleaned[-1][1] 
            
            # add that page to the cleaned timeline
            timeline_cleaned.append([timeline[i][0][0], timeline[i][1],
                                     'temp_time'])
            
    timeline_cleaned[-1][1] = timeline[i][1] - timeline_cleaned[-1][1] 
    timeline_cleaned[-1][2] = timeline[i][1]

    for i in range(len(timeline_cleaned)):
            timeline_cleaned[i][0] = timeline_cleaned[i][0][:-4]

    
    ### WRITING TO A FILE ###
    csv_title = "timings-" + video_title[:-4] + ".csv"
    filepath = os.path.join(output_folder_path, csv_title)
    with open(filepath, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        if args.header == True:
            # write a header.
            writer.writerow(['Screen_Title','Time_Taken_(Seconds)', 
                             'Cumulative_Time_(Seconds)'])
        for row in timeline_cleaned:
            writer.writerow(row)
    if args.verbose:
        print(csv_title + " written.")
        csv_file.close()

    #########################
gc.collect()

