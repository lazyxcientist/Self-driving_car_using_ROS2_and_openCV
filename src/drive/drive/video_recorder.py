from typing import List
import rclpy
from rclpy.context import Context
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Image


import cv2
from cv_bridge import CvBridge


class Video_get(Node):
    def __init__(self):
        super().__init__('video_subscriber')

        self.subscriber = self.create_subscription(Image, '/camera/image_raw' , self.process_data, 10)

        # opencv settings
        self.out = cv2.VideoWriter('output.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 30, (1280,720))
        self.bridge = CvBridge()


    def process_data(self, data):

        frame = self.bridge.imgmsg_to_cv2(data,'bgr8') #converting
        self.out.write(frame)
        cv2.imshow("output",frame)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    image_subscriber = Video_get()
    rclpy.spin(image_subscriber)
    rclpy.shutdown()

if __name__ == '__main__':
    main()