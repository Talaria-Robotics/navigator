#!/usr/bin/python3

import socket
import json
import lidar
import encoder
import numpy as np
import vector as vec
from time import sleep
from threading import Thread

controlMotors = False

if controlMotors:
    import speed_control as sc

class SCUTTLE:

    def __init__(self):

        # Kinematics
        self.wheelRadius = 0.04
        self.wheelBase = 0.1
        self.A_matrix = np.array([[1/self.wheelRadius, -self.wheelBase/self.wheelRadius], [1/self.wheelRadius, self.wheelBase/self.wheelRadius]])
        self.max_xd = 0.4
        self.max_td = (self.max_xd/self.wheelBase)

        # LIDAR UDP
        self.IP = "127.0.0.1"
        self.port = 3553
        self.lidarSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lidarSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lidarSock.bind((self.IP, self.port))
        self.lidarSock.settimeout(.25)
        
        # Left encoder UDP
        self.encoderLSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.encoderLSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.encoderLSock.bind((self.IP, self.port))
        self.encoderLSock.settimeout(.25)
        
        # Right encoder UDP
        self.encoderRSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.encoderRSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.encoderRSock.bind((self.IP, self.port))
        self.encoderRSock.settimeout(.25)

        # NodeRED data in
        self.dashBoardData = None

        # LIDAR Thread
        lidar.init()
        lidarThread = Thread(target=self.scan_loop, daemon=True)
        lidarThread.start()

        # NodeRED Data Thread
        self.dashBoardDataThread = Thread(target=self._dashBoardDataLoop, daemon=True)
        self.dashBoardDataThread.start()

        # Driving Thread
        self.controlThread = Thread(target=self._controlLoop, daemon=True)
        self.controlThread.start()

    def scan_loop(self):
        while True:
            data1, data2 = self.cartesian_scan()
            data_msg = data1.encode('utf-8')
            self.lidarSock.sendto(data_msg, ("127.0.0.1", 3555))
            data_msg = data2.encode('utf-8')
            self.lidarSock.sendto(data_msg, ("127.0.0.1", 3558))
            
            # Read encoder positions
            encL_val, encR_val = encoder.readShaftPositions()
            print(f"Left: {encL_val}\tRight: {encR_val}")

            # Send encoder data to dashboard
            self.encoderLSock.sendto(str(encL_val).encode('utf-8'), ("127.0.0.1", 3556))
            self.encoderRSock.sendto(str(encR_val).encode('utf-8'), ("127.0.0.1", 3557))
            
            sleep(.025)

    def cartesian_scan(self):
        rows = ''
        polar_data = lidar.scan()

        for t, d in polar_data:
            cartesian_point = vec.polar2cart(d,t)
            rows += self.format_row(cartesian_point)

        return rows[:-1]

    # Format the x,y lidar coordinates so that the bubble-chart can display them
    def format_row(self, point: complex, r=3):
        x, y = point.real, point.imag
        return '{x: ' + str(x) + ', y: ' + str(y) + ', r:' + str(r) + '},'

    def _dashBoardDataLoop(self):
        while True:
            try:
                dashBoardData,recvAddr = self.lidarSock.recvfrom(1024)
                self.dashBoardData = json.loads(dashBoardData)

            except socket.timeout:
                self.dashBoardData = None

    def _controlLoop(self):
        while True:
            if self.dashBoardData != None:
                try:
                    userInputTarget = self.dashBoardData['one_joystick']
                    wheelSpeedTarget = self._getWheelSpeed(userInputTarget)
                    if controlMotors:
                        sc.driveOpenLoop(wheelSpeedTarget)
                except: 
                    pass

    def _getWheelSpeed(self,userInputTarget):
        try:
            robotTarget = self._mapSpeeds(np.array([userInputTarget['y'],-1*userInputTarget['x']]))
            wheelSpeedTarget = self._calculateWheelSpeed(robotTarget)
            return wheelSpeedTarget
        except:
            pass
    
    def _mapSpeeds(self,original_B_matrix):
        B_matrix = np.zeros(2)
        B_matrix[0] = self.max_xd * original_B_matrix[0]
        B_matrix[1] = self.max_td * original_B_matrix[1]
        return B_matrix

    def _calculateWheelSpeed(self,B_matrix):
        C_matrix = np.matmul(self.A_matrix,B_matrix)
        C_matrix = np.round(C_matrix,decimals=3)
        return C_matrix


    def getdashBoardData(self):
        return self.dashBoardData


if __name__ == "__main__":
    robot = SCUTTLE()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        lidar.disconnect()
        print("Stopping robot")
