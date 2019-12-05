#!/usr/bin/env python

import roslib
roslib.load_manifest('ping360_sonar')

from sensor import Ping360
import argparse
import cv2
import numpy as np
from math import pi, cos, sin
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import rospy

          
def main():
     parser = argparse.ArgumentParser(description="Ping python library example.")
     parser.add_argument('--device', action="store", required=True, type=str, help="Ping device port.")
     parser.add_argument('--baudrate', action="store", type=int, default=2000000, help="Ping device baudrate.")
     parser.add_argument('--v', action="store", type=bool, default=False, help="Verbose")
     parser.add_argument('--size', action="store", type=int, default=200, help="Image Size")

     args = parser.parse_args()
     try:
          rospy.init_node('ping360_node')
          transmitFrequency = 1000
          samplePeriod = 80
          numberOfSample = 200
          speedOfSound = 1450
          length = args.size 
          step = 1
          angle = 0
          topic = "ping360_sonar"
          queue_size= 1

          p = Ping360(args.device, args.baudrate)
          imagePub = rospy.Publisher(topic, Image, queue_size=queue_size)
          bridge = CvBridge()

          print("Initialized: %s" % p.initialize())
          p.set_transmit_frequency(transmitFrequency)
          p.set_sample_period(samplePeriod)
          p.set_number_of_samples(numberOfSample)

          max_range = samplePeriod * numberOfSample * speedOfSound / 2
          image = np.zeros((length, length, 1), np.uint8)
          center = (float(length/2),float(length/2))
          while not rospy.is_shutdown():
               p.transmitAngle(angle)
               data = bytearray(getattr(p,'_data'))
               data_lst = [k for k in data]
               linear_factor = float(len(data_lst))/float(center[0])
               for i in range(int(center[0])):
                    if(i < center[0]*max_range/max_range):
                         pointColor = data_lst[int(i*linear_factor-1)]
                    else:
                         pointColor = 0
                    for k in np.linspace(0,step,8*step):
                         theta = 2*pi*(angle+k)/400.0
                         x = float(i)*cos(theta)
                         y = float(i)*sin(theta)
                         image[int(center[0]+x)][int(center[1]+y)][0] = pointColor

               angle = (angle + step) % 400
               if args.v:
                    cv2.imshow("PolarPlot",image)
                    cv2.waitKey(27)
               publish(image, imagePub, bridge)
               rospy.sleep(0.1)
     
     except KeyboardInterrupt:
          print("Shutting down")
          cv2.destroyAllWindows()

def publish(image, imagePub, bridge):
     try:
          imagePub.publish(bridge.cv2_to_imgmsg(image, "mono8"))
     except CvBridgeError as e:
          print(e)