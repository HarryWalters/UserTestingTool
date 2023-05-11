#plottingMetrics
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.axes as axes
import argparse
import os
from tqdm import tqdm # for pretty loading bars
import shutil # for pretty displaying on the terminal

"""
Plotting Metrics

This script generates a horizontal stacked bar chart from data in a csv file(s). The chart displays the time spent on each page of an application, along with transitions between pages.

Usage: python3 plottingMetrics.py <path/to/app_screenshots> <path/to/metrics_data>

Args:
    app_screenshots (str): Path to the app screenshots, needed to produce the labels on the y axis.
    metrics_data (str): Path to the metrics data. 
                        If you provide a directory, it will process all the data in the directory.
                        If you provide a file (or list of files), it will process the file(s) listed.
    plot_type (str, optional): The filetype which we save the plots in. Defaults to ".svg".)
    

Output:
    A horizontal stacked bar chart saved as an svg file.

Example:
    python plottingMetrics.py metrics_data/timings-WM.csv

Dependencies:
    - numpy
    - matplotlib
    - argparse
    - os
    - tqdm
    - shutil
"""

def stringOrList(arg_value):
    output = arg_value #If it's a single file, or a single directory name, keep it as is.
    if "," in arg_value:
        output = arg_value.split(",")
        if output[0][0] == "[": # if the first character of the first file has [,
            output[0] = output[0][1:] # get rid of it
        if output[len(output)-1][-1] == "]": # if the last character of the last file has ],
            output[len(output)-1] = output[len(output)-1][:-1] # get rid of it.
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
    default=".",
    help="Path to the App Screens Directory.\n"
         "Ensures that your plot(s) show all the pages on the y axis.")

parser.add_argument(
    "metrics_data",
    type=stringOrList,
    default=".",
    help="Path to the metrics data.\n"
         "If you provide a directory, it will process all the data in the directory.\n"
         "If you provide a file (or list of files), it will process the file(s) listed.")

parser.add_argument(
    "--output_plot_directory",
    type=str,
    default="generated_plots",
    help="The name of the folder where we'll save our generated plots. Default = 'generated_plots'")
    
parser.add_argument(
    "--additional_image_types",
    type=stringOrList,
    default="",
    help='If your image screenshots are of an unconventional filetype, enter the filetype(s) here. Default = ""')
    
parser.add_argument(
    "--plot_type",
    type=str,
    default=".svg",
    help='Specify the output image filetype. Default=".svg"')

parser.add_argument(
    "--header",
    type=bool,
    default=True,
    help="Specifies whether the first column of the file(s) are headers. Default = True")

args = parser.parse_args()

folder_name = args.output_plot_directory.split("/")[-1].split("\\")[-1]
output_folder_path = os.path.join(os.getcwd(), folder_name)

if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)


# IF THE USER SPECIFIES ONE OR MORE .CSV FILES ##

if type(args.metrics_data) == list:
    csv_names = args.metrics_data
elif type(args.metrics_data) == str:
    if args.metrics_data[-4:].lower() == ".csv":
        csv_names = [args.video_recording]
    else:
        csv_names = getFileNames(args.metrics_data, [".csv"])
        
#################################################



############# ADDITIONAL FILETYPES ##############

image_extensions = [".jpg", ".jpeg", ".png",".raw"]
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

page_names = getFileNames(args.app_screens_directory, image_extensions)
page_names = [filename[:-4].split("/")[-1] for filename in page_names]


#################################################

for filename in csv_names:
    data = []
    #filename = "timings-WM.csv"
    with open(filename, "r") as fp:
        if args.header == True:
            line = fp.readline() # Ignore the first line, it's a header
        line = fp.readline()
        while line != "":
            temp_row = line.strip().split(",")
            # if the user decides to add their own custom pages (which don't 
            # correspond with the app_screenshots folder)
            if temp_row[0] not in page_names:
                if temp_row[0] != "low confidence detection":
                    page_names.append(temp_row[0])
            data.append([temp_row[0], float(temp_row[1]), float(temp_row[2])])
            line = fp.readline()
    total_seconds = float(temp_row[2]) # the last line read
    # every x value gets a bar that's invisible EXCEPT for the x value
    # mentioned in the current line
    fig, ax = plt.subplots()


    bottom = np.zeros(len(page_names))
    transition_colour = "pink"
    box_colour = "blue"
    old_idx = page_names.index(data[0][0])
    transition_thickness = 0.5
    loading_bar_message = "Loading " + filename + "..."
    columns, _ = shutil.get_terminal_size() 
    bar_width = int(columns*0.8)
    
    for i, line in tqdm(enumerate(data), total=len(data), ncols=bar_width,
                        desc=loading_bar_message, bar_format="{l_bar}{bar}|"):
            if i > 0: # If we're looking at any page, other than the first one,
                # draw a line connecting the two rectangles
                new_idx = page_names.index(line[0])
                # sort them
                low_idx, high_idx = min(old_idx, new_idx), max(old_idx,new_idx)
                temp_bottom = [0 for i in range(len(page_names))]
                for i in range(low_idx, high_idx):
                    temp_bottom[i] += transition_thickness
                ax.barh(page_names, width = temp_bottom, label = line[0],
                        left=bottom, color = transition_colour, align='edge',
                        height=1)
                old_idx = new_idx
            temp_row = [0 for i in range(len(page_names))]
            temp_row[page_names.index(line[0])] = line[1]
            ax.barh(page_names, width = temp_row, label = line[0], left=bottom,
                    color = box_colour)
            bottom += np.full(len(page_names), line[1])

    ax.set_title("App Usage\n", fontsize=20)
    total_seconds_cleaned = round(total_seconds/10)*10 + 10
    plt.xticks(range(0, int(total_seconds_cleaned), 10))

    plot_filename = filename[:-4] # takes away the extension name
    plt.xlabel("Seconds", fontsize=12)

    # This adds the message at the end of the loading bar.
    print("    Saving " + plot_filename + args.plot_type + "..." + " "*8,
          end="", flush=True)
    
     # make sure it's just the filename here
    plot_filename = plot_filename.split("/")[-1].split("\\")[-1]
    if "." not in args.plot_type:
        extension = "." + args.plot_type
    else:
        extension = args.plot_type
        
    plot_filename += extension
    filepath = os.path.join(output_folder_path, plot_filename)
    if args.plot_type != ".svg":
        plt.savefig(filepath, bbox_inches='tight', dpi = 300)
    else:
        plt.savefig(filepath, bbox_inches='tight')
        
    tqdm.write("Done.")
