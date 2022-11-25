import os
import shutil
import subprocess

from msk.jointlandmarks import joints_list_to_csv, post_process_tracker_csv
from msk.mks_plotter import mediapose_mks_plotter, plot_filtered_tracker_video

tracker_csv_dir_name = 'tracker_csvs'
mediapose_mks_dir_name = 'mediapose_mks'
filtered_mks_dir_name = 'filtered_mks'
uploaded_videos_dir_name = 'uploaded_videos'

def video_converter(input_: str, output: str) -> None:
    subprocess.run(['ffmpeg', '-y', '-i', input_, output])
    return

def get_name_from_path(file_path):
    file_name =  file_path.split(os.sep)[-1]
    return file_name.split('.')[0]


def create_tracker_paths(file_path):
    """
    Given a file name returns a tuple of paths (if they don't exist, placeholders will be created) for
    1. tracker_csv
    2. annotated video
    3. filtered annotated  video
    """

    file_name = get_name_from_path(file_path)

    # Create a directory for tracker_csvs
    if not os.path.exists(tracker_csv_dir_name):
        os.makedirs(tracker_csv_dir_name, exist_ok=True)

    # Create a directory for vanilla mediapose MKS
    if not os.path.exists(mediapose_mks_dir_name):
        os.makedirs(mediapose_mks_dir_name, exist_ok=True)

    # Create a directory for filtered mediapose MKS
    if not os.path.exists(filtered_mks_dir_name):
        os.makedirs(filtered_mks_dir_name, exist_ok=True)

    output_annotated_video = f"{os.path.join(mediapose_mks_dir_name, file_name)}_joint_tracker.avi"
    output_tracker_file = f"{os.path.join(tracker_csv_dir_name, file_name)}_joint_tracker.csv"
    output_filt_video = f"{os.path.join(filtered_mks_dir_name, file_name)}_joint_tracker_filtered.avi"

    return output_tracker_file, output_annotated_video, output_filt_video

def upload_video(bytes_data: bytes, file_path: str) -> None:
    # Delete everything in file_path before uploading the video
    try:
        shutil.rmtree(uploaded_videos_dir_name)
    except FileNotFoundError:
        pass

    # Create a place holder for videos uploaded
    if not os.path.exists(uploaded_videos_dir_name):
        os.makedirs(uploaded_videos_dir_name, exist_ok=True)

    with open(file_path, 'wb') as f:
        f.write(bytes_data)


def get_video_bytes(video_path: str):
    """
    Shows video on the streamlit page
    """
    with open(video_path, 'rb') as f:
        bytes = f.read()
        return bytes


def video_exists(filtered_video_path) -> bool:
    return os.path.exists(filtered_video_path)

class UploadedFile:

    def __init__(self, file_path):

        self.file_path = file_path

        # Create tracker paths
        self.tracker_path, self.annotated_video_path, self.filt_video_path = create_tracker_paths(file_path)


    def process_video(self) -> str:
        """
        1. Generate MKS overlay for the video
        2. Output a tracker list csv
        3. Create a filtered video output
        """

        # 1. Generate MKS overlay for the video
        joint_tracker_list, img_width, img_height = mediapose_mks_plotter(self.file_path, self.annotated_video_path)

        # 2. Output a tracker list csv
        joints_list_to_csv(joint_tracker_list, self.tracker_path)
        print(f"Tracker csv created - {self.tracker_path}")

        # Post processing the joint tracker
        print("Post processing the video")
        # Post process tracker csv
        df_to_plot = post_process_tracker_csv(self.tracker_path, img_height)
        df_to_plot.to_csv(self.tracker_path, index=False)
        print(f"Tracker csv updated with filtered signals - {self.tracker_path}")

        # 3. Create a filtered video output
        # MKS plotter with filtered signals
        plot_filtered_tracker_video(self.file_path, self.filt_video_path, df_to_plot)

        print("Filtered MKS video created")

        # Convert annotated video to mp4
        print(f"Converting {self.annotated_video_path} to mp4")
        annotated_video_mp4 = self.annotated_video_path.split('.')[0] + '.mp4'
        video_converter(self.annotated_video_path, annotated_video_mp4)

        # Convert the filtered video to mp4
        print(f"Converting {self.filt_video_path} to mp4")
        mp4_filtered_file_name = self.filt_video_path.split('.')[0] + '.mp4'
        video_converter(self.filt_video_path, mp4_filtered_file_name)

        return mp4_filtered_file_name
