import math
import threading
from time import sleep
from typing import List

from .ObjectDetectionListener import DetectedObject
from .ObjectDetectionListener import IObjectDetectionListener
from .PoseUpdater import GroundTruthPoseUpdater
from .PoseUpdater import IPoseUpdater
from .PositionListener import IPositionListener
from .Robot import Pose
from .Robot import Robot


class RobotMonitor(threading.Thread):
    def __init__(self, robot: Robot, poseUpdater: IPoseUpdater, stopEvent: threading.Event, intervalMs=200):
        threading.Thread.__init__(self)
        self.robot = robot
        self.poseUpdater = poseUpdater
        self.gtPoseUpdater = GroundTruthPoseUpdater()
        self.intervalSeconds = intervalMs / 1000
        self.stopEvent = stopEvent
        self.frontObjDetecListeners = []
        self.positionListeners = []
        self.lastRobotPose = Pose()

    def run(self):
        while not self.stopEvent.is_set():
            self.update()
            sleep(self.intervalSeconds)

    def update(self):
        self.robot.updateSensors()
        self.lastRobotPose = self.robot.pose
        self.robot.gtPose = self.gtPoseUpdater.update(self.robot)
        self.robot.pose = self.poseUpdater.update(self.robot)

        self.readPosition()
        self.readSonarReadings()

    def readSonarReadings(self):
        # FIXME: robot should know the position of each sonar
        # 0: 90
        # 1: 50
        # 2: 30
        # 4: 10
        # 5: -10
        # ...
        angles = [math.radians(x) for x in [90, 50, 30, 10, -10, -30, -50, -90]]
        detectedObjs = []
        for i in range(0, 8):
            if self.robot.sonarReading[i] != -1:
                detectedObjs.append(DetectedObject(self.robot.sonarReading[i], angles[i], i))

        self.__frontObjectDetected(detectedObjs)

    def readPosition(self):
        if self.lastRobotPose != self.robot.pose:
            self.__positionChanged(self.robot.pose)

    def subscribeToFrontObjectDetection(self, listener: IObjectDetectionListener):
        self.frontObjDetecListeners.append(listener)

    def subscribeChangePosition(self, listener: IPositionListener):
        self.positionListeners.append(listener)

    def __frontObjectDetected(self, detectedObjs: List[DetectedObject]):
        for l in self.frontObjDetecListeners:
            l.objectDetected(detectedObjs)

    def __positionChanged(self, pose):
        for l in self.positionListeners:
            l.newPosition(pose)
