import mediapipe as mp
import pandas as pd
import cv2
from typing import List, Tuple

from mediapipe.python.solutions.pose_connections import POSE_CONNECTIONS

from msk.jointlandmarks import JointLandMarks, joint_names


def mediapose_mks_plotter(input_file_path: str, annotated_video: str) -> Tuple[List[List[float]], int, int]:
    """
    Returns: a List of x, y, z coordinates of joints, image_width and image_height
    """
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_pose = mp.solutions.pose

    cap = cv2.VideoCapture(input_file_path)

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    joint_tracker_list = []

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(annotated_video, fourcc, 10, (frame_width, frame_height))
    with mp_pose.Pose(
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.95) as pose:
        frame = 0
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                # If loading a video, use 'break' instead of 'continue'.
                break
            # print(f"Height: {cap.get(3)}")
            # print(f"Width: {cap.get(4)}")
            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            if results.pose_landmarks:
                ele = results.pose_landmarks.ListFields()[0][1]  # This list needs to be sent to jointlandmarks
                joint_landmarks = JointLandMarks(ele, frame_width, frame_height)
                joint_tracker_list.append(joint_landmarks.get_joint_landmarks())

            # Draw the pose annotation on the image.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )

            image = cv2.putText(image, f"Frame-{frame}", (frame_width - 300, frame_height - 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 0, 255), 2)

            out.write(image)

            frame = frame + 1

            if cv2.waitKey(1) == ord('q'):
                break

    out.release()
    cap.release()
    cv2.destroyAllWindows()

    print(f"Video file created - {annotated_video}")

    return joint_tracker_list, frame_width, frame_height


def get_joint_xy(joint_number: Tuple, joints_frame: pd.Series) -> Tuple:
    # Get the joint_name from joint_number
    joint_name = joint_names[joint_number]
    return int(joints_frame[f"{joint_name}_x_filt"]), int(joints_frame[f"{joint_name}_y_filt"])


def draw_filtered_connections(image, joints_series_frame: pd.Series) -> None:
    # Get the connections to draw
    for pair in iter(POSE_CONNECTIONS):
        # Get pairs x,y coordinates
        p1 = get_joint_xy(pair[0], joints_series_frame)
        p2 = get_joint_xy(pair[1], joints_series_frame)

        # Add markers to p1 and p2
        cv2.drawMarker(image, p1, (0, 0, 255),
                       markerType=cv2.MARKER_STAR, markerSize=5,
                       thickness=2)
        cv2.drawMarker(image, p2, (0, 0, 255),
                       markerType=cv2.MARKER_STAR, markerSize=5,
                       thickness=2)

        # Draw marker from p1 to p2
        cv2.line(image, p1, p2, (50, 205, 50), thickness=2,
                 lineType=cv2.LINE_4)
    return


def plot_filtered_tracker_video(path_to_raw_video: str, path_to_filtered_video: str, filtered_df: pd.DataFrame) -> None:
    cap = cv2.VideoCapture(path_to_raw_video)

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    # Realign columns in filtered_df
    y_column_names = [col_name for col_name in filtered_df.columns if col_name[-7:] == '_y_filt']
    filtered_df[y_column_names] = filtered_df[y_column_names].transform(lambda x: frame_height - x)

    # This works for .avi videos
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(path_to_filtered_video, fourcc, 10, (frame_width, frame_height))
    frame = 0
    while cap.isOpened():
        success, image = cap.read()
        if not success or (frame == filtered_df.shape[0]):
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            break
            # print(f"Height: {cap.get(3)}")
            # print(f"Width: {cap.get(4)}")
            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Draw the pose annotation on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        draw_filtered_connections(image, filtered_df.iloc[frame, :])

        image = cv2.putText(image, f"Frame-{frame}", (frame_width - 300, frame_height - 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 2)

        out.write(image)

        frame = frame + 1

        if cv2.waitKey(1) == ord('q'):
            break

    out.release()
    cap.release()
    cv2.destroyAllWindows()

    return