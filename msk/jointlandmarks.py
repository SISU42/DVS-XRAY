import numpy as np
import pandas as pd
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark
from itertools import chain

from typing import List
import csv

from msk.filtering import filter_signal

joint_names = ['nose', 'left_eye_inner', 'left_eye', 'left_eye_outer', 'right_eye', 'right_eye_outer',
               'right_eye_outer', 'left_ear', 'right_ear', 'mouth_left', 'mouth_right', 'left_shoulder',
               'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_pinky',
               'right_pinky', 'left_index', 'right_index', 'left_thumb', 'right_thumb', 'left_hip', 'right_hip',
               'left_knee', 'right_knee', 'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
               'left_foot_index', 'right_foot_index']
joint_names_dict = {}
for index, val in enumerate(joint_names):
    joint_names_dict[val] = index


def get_joints_xyz_list() -> List[str]:
    result = []

    for joint_name in joint_names:
        result.extend(add_x_y_z(joint_name))

    return result


def add_x_y_z(joint_name: str) -> List[str]:
    return [f"{joint_name}_x", f"{joint_name}_y", f"{joint_name}_z"]


joint_names_xyz_list = get_joints_xyz_list()


def joints_list_to_csv(joint_landmarks_list: List[List[float]], output_file_path: str) -> None:
    """
    Creates a csv file from a list of joint landmarks
    """

    # for joint_name in joint_names:
    #     joint_names_xyz_list.extend(add_x_y_z(joint_name))

    with open(output_file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=joint_names_xyz_list)

        writer.writeheader()

        for joints_frame in joint_landmarks_list:
            row_to_write = dict(zip(joint_names_xyz_list, list(chain(*joints_frame))))
            writer.writerow(row_to_write)


def post_process_tracker_csv(tracker_csv_path: str, image_height: int) -> pd.DataFrame:
    df = pd.read_csv(tracker_csv_path)

    # Realign image origin to the lower left corner of the image. This is done only for y signals by subtracting the
    # image height
    y_column_names = [col_name for col_name in df.columns if col_name[-2:] == '_y']
    df[y_column_names] = df[y_column_names].transform(lambda x: image_height - x)

    # Add a filter transform and _filt suffix to the filtered signals
    filt_df = df \
        .transform(filter_signal) \
        .add_suffix('_filt')

    df_to_plot = pd.concat([df, filt_df], axis=1)

    # Add a frames column
    df_to_plot['frames'] = np.arange(1, df_to_plot.shape[0]+1)

    return df_to_plot


class JointLandMarks:

    def __init__(self, ele_list: List[NormalizedLandmark], width: float, height: float):
        self.ele_list = ele_list
        self.width = width
        self.height = height

    @staticmethod
    def extract_coordinate_from_landmark(ele: NormalizedLandmark, dim: int) -> float:
        """
        Get the coordinate from NormalizedLandmark object
        :param ele: NormalizedLandmark object
        :param dim: 0 for x, 1 for y, 2 for z
        :return:
        """
        return ele.ListFields()[dim][1]

    def get_joint_landmarks(self):
        """
        Returns joint landmarks as a list of x,y,z coordinates
        :return:
        """
        result = []

        for ele in self.ele_list:
            ele_x = JointLandMarks.extract_coordinate_from_landmark(ele, 0) * self.width
            ele_y = JointLandMarks.extract_coordinate_from_landmark(ele, 1) * self.height
            ele_z = JointLandMarks.extract_coordinate_from_landmark(ele, 2)
            result.append([ele_x, ele_y, ele_z])

        return result
