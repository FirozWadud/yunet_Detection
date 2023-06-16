# This file is part of OpenCV Zoo project.
# It is subject to the license terms in the LICENSE file found in the same directory.
#
# Copyright (C) 2021, Shenzhen Institute of Artificial Intelligence and Robotics for Society, all rights reserved.
# Third party copyrights are property of their respective owners.

import argparse
from itertools import product

import numpy as np
import cv2 as cv

class YuNet:
    def __init__(self, modelPath, confThreshold=0.6, nmsThreshold=0.3, topK=5000, backendId=0, targetId=0):
        self._modelPath = modelPath
        self._confThreshold = confThreshold
        self._nmsThreshold = nmsThreshold
        self._topK = topK
        self._backendId = backendId
        self._targetId = targetId

        self._model = cv.FaceDetectorYN.create(
            model=self._modelPath,
            config="",
            input_size=(0, 0),  # Initialize with default size of (0, 0)
            score_threshold=self._confThreshold,
            nms_threshold=self._nmsThreshold,
            top_k=self._topK,
            backend_id=self._backendId,
            target_id=self._targetId)

    # Rest of the code

    def setInputSize(self, input_size):
        self._model.setInputSize(input_size)


    @property
    def name(self):
        return self.__class__.__name__

    def setBackendAndTarget(self, backendId, targetId):
        self._backendId = backendId
        self._targetId = targetId
        self._model = cv.FaceDetectorYN.create(
            model=self._modelPath,
            config="",
            input_size=self._inputSize,
            score_threshold=self._confThreshold,
            nms_threshold=self._nmsThreshold,
            top_k=self._topK,
            backend_id=self._backendId,
            target_id=self._targetId)

    def setInputSize(self, input_size):
        self._model.setInputSize(tuple(input_size))

    def infer(self, image):
        # Forward
        faces = self._model.detect(image)
        return faces[1]

def visualize(image, results, box_color=(0, 255, 0), text_color=(0, 0, 255), fps=None):
    output = image.copy()
    landmark_color = [
        (255,   0,   0), # right eye
        (  0,   0, 255), # left eye
        (  0, 255,   0), # nose tip
        (255,   0, 255), # right mouth corner
        (  0, 255, 255)  # left mouth corner
    ]

    if fps is not None:
        cv.putText(output, 'FPS: {:.2f}'.format(fps), (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, text_color)

    for det in (results if results is not None else []):
        bbox = det[0:4].astype(np.int32)
        cv.rectangle(output, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), box_color, 2)

        conf = det[-1]
        cv.putText(output, '{:.4f}'.format(conf), (bbox[0], bbox[1]+12), cv.FONT_HERSHEY_DUPLEX, 0.5, text_color)

        landmarks = det[4:14].astype(np.int32).reshape((5,2))
        for (x, y), color in zip(landmarks, landmark_color):
            cv.circle(output, (x, y), 1, color, -1)

    return output

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='YuNet Demo')
    parser.add_argument('--model', type=str, required=True, help='Path to the YuNet model')
    args = parser.parse_args()

    # Initialize YuNet model
    model = YuNet(args.model)

    # Initialize video capture
    cap = cv.VideoCapture("rtsp://admin:admin123@192.168.0.150:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif")

    # Check if camera opened successfully
    if not cap.isOpened():
        print("Error opening video capture.")
        return

    # Create a frame buffer
    buffer_size = 5  # Adjust the buffer size as needed
    frame_buffer = []

    # Start capturing frames
    frame_counter = 0
    drop_rate = 2  # Adjust the frame drop rate as needed

    while cv.waitKey(1) < 0:
        hasFrame, frame = cap.read()
        if not hasFrame:
            print('No frames grabbed!')
            break
        w = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        model.setInputSize([w, h])
        frame_counter += 1

        # Skip frames based on the drop rate
        if frame_counter % drop_rate != 0:
            continue

        # Resize the frame to the expected input size


        # Add the frame to the buffer
        frame_buffer.append(frame)

        # Process frames from the buffer
        if len(frame_buffer) >= buffer_size:
            # Inference
            tm = cv.TickMeter()
            tm.start()
            results = model.infer(frame_buffer.pop(0))  # Process the oldest frame in the buffer
            tm.stop()

            # Draw results on the input image
            frame_with_results = visualize(frame, results, fps=tm.getFPS())

            # Visualize results in a new Window
            cv.imshow('YuNet Demo', frame_with_results)

            tm.reset()

    # Release video capture
    cap.release()

    # Close all OpenCV windows
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()