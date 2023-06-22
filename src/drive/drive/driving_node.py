import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from cv_bridge import CvBridge


'''
twist datatype containts
	x,y,z, r,p,Y(upper side rotation)
'''

class Car_driver(Node):
    def __init__(self):
        super().__init__('driving_node')
        self.publisher = self.create_publisher(Twist, '/cmd_vel',40)

        self.timer = self.create_timer(0.5, self.send_cmd_vel)

        self.velocity = Twist()
        self.bridge = CvBridge()


    def send_cmd_vel(self):
        self.velocity.linear.x = 0.0
        self.velocity.angular.z = 0.0
        self.publisher.publish(self.velocity)

    


def main(args=None):
    rclpy.init(args=args)
    driver = Car_driver()
    rclpy.spin(driver)
    rclpy.shutdown()


if __name__ == "__main__":
    main()