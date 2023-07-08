import cv2
from .Detection.Lanes.lane_detection import detect_lanes
# from .Detection.Lanes.Lane_Detection import detect_Lane
from .Detection.Signs.sign_detection import detect_signs
# from .Detection.TrafficLights.TrafficLights_Detection import detect_TrafficLights
import cv2
from numpy import interp
from .config import config
# 4 Improvements that will be done in (Original) SDC control algorithm
# a) lane assist had iregular steering predictions
#    Solution : use rolling average filter
# b) Considering road is barely 1.5 car wide. A quarter of Image width for distance from the road mid 
#                                             from the predicted road center seems bit too harsh
#    Solution:  Increase to half of image width
# c) Car was drifting offroad in sharper turns causing it to lose track of road
#    Solution: Increase weightage of distance (road_center <=> car front) from 50% to 65% 
#              So steers more in case it drift offroad
# d) Car not utilizing its full steering range causing it to drift offroad in sharp turns
#    Solution: Increase car max turn capability

# 2 additons to Drive_Bot.py
# a) 1 control block added for enable/disable Sat_Nav feature
# b) Track Traffic Light and Road Speed Limits (State)  ==> Essential for priority control mechanism 
#                                                           That we will create for integrating Sat_Nav 
#                                                           ability to the SDC

from collections import deque

class Control():
    def __init__(self):
        self.angle = 0.0
        self.speed = 80
        # Cruise_Control Variable
        ###################
        ######## turn 
        self.prev_Mode = "Detection"
        self.IncreaseTireSpeedInTurns = False

        ######################
        ## left turn sign
        # Nav T-Junc Variable
        self.prev_Mode_LT = "Detection"
        self.Left_turn_iterations = 0
        self.Frozen_Angle = 0
        self.Detected_LeftTurn = False
        self.Activat_LeftTurn = False



    def follow_lane(self, max_sane_dist, dist , curv , mode , tracked_class):

        ###################################
        ########## turn 
        #2. Cruise control speed adjusted to match road speed limit
        if((tracked_class!=0) and (self.prev_Mode == "Tracking") and (mode == "Detection")):
            if  (tracked_class =="speed_sign_30"):
                self.speed = 30
            elif(tracked_class =="speed_sign_60"):
                self.speed = 60
            elif(tracked_class =="speed_sign_90"):
                self.speed = 90
            elif(tracked_class =="stop"):
                self.speed = 0
                print("Stopping Car !!!")
            
        self.prev_Mode = mode # Set prevMode to current Mode
        ####################################




        self.speed = 80
        max_turn_angle = 90
        max_turn_angle_neg = -90
        req_turn_angle = 0 ## change, 

        # calculating require turn angle 
        if ( (dist>max_sane_dist) or (dist< (-1*max_turn_angle))):
            if (dist>max_sane_dist):
                req_turn_angle = max_turn_angle + curv
            else:
                req_turn_angle = max_turn_angle_neg + curv

        else:
            car_offset = interp(dist, [-max_sane_dist,max_sane_dist], [-max_turn_angle,max_turn_angle])
            req_turn_angle = car_offset + curv

        # handle overflow
        if (req_turn_angle > max_turn_angle) or (req_turn_angle < max_turn_angle_neg):
            if (req_turn_angle> max_turn_angle):
                req_turn_angle = max_turn_angle
            else:
                req_turn_angle = max_turn_angle_neg

        ## handle max car turn ablility , because car can turn 45 degrees only
        self.angle = interp(req_turn_angle, [max_turn_angle_neg,max_turn_angle], [-45,45]) #interpulate




        ################################
        ############## turn
         
        #handle overflow
        if ((req_turn_angle>max_turn_angle)or (req_turn_angle<max_turn_angle_neg)):
            if (req_turn_angle>max_turn_angle):
                req_turn_angle = max_turn_angle
            else:
                req_turn_angle = max_turn_angle_neg
        # Handle max car turn ability
        self.angle = interp(req_turn_angle,[max_turn_angle_neg,max_turn_angle],[-45,45])
        if (self.IncreaseTireSpeedInTurns and (tracked_class !="left_turn")):
            if(self.angle>30):
                car_speed_turn = interp(self.angle,[30,45],[80,100])
                self.speed = car_speed_turn
            elif(self.angle<(-30)):
                car_speed_turn = interp(self.angle,[-45,-30],[100,80])
                self.speed = car_speed_turn

        ###########################

    def drive(self, Current_state):
        [dist, curv, img ,mode , tracked_class] =  Current_state

        if (dist != 1000) and (curv != 1000) :
            self.follow_lane(img.shape[1]/4,  dist, curv , mode , tracked_class)
        
        else:
            self.speed = 0.0 # stop the car if lane ditection is stoped


        ############### 
        ## left turn sign

        if (tracked_class == "left_turn"):
            self.Obey_LeftTurn(mode)


        # interpolating the angle and speed from real world to motor world
        self.angle = interp(self.angle , [-45, 45], [0.5, -0.5]) # change the angle from range 45 to range 0.5
        self.speed = interp(self.speed , [30, 90], [1, 2])




    def Obey_LeftTurn(self,mode):

        self.speed = 50
        # Car starts tracking left turn...
        if ( (self.prev_Mode_LT =="Detection") and (mode=="Tracking")):
            self.prev_Mode_LT = "Tracking"
            self.Detected_LeftTurn = True 
        elif ( (self.prev_Mode_LT =="Tracking") and (mode=="Detection")):
            self.Detected_LeftTurn = False
            self.Activat_LeftTurn = True
            # Move left by 7 degree every 20th iteration after a few waiting a bit 
            if ( ((self.Left_turn_iterations % 20 ) ==0) and (self.Left_turn_iterations>100) ):
                self.Frozen_Angle = self.Frozen_Angle -7
            
            # After a time period has passed [ De-Activate Left Turn + Reset Left Turn Variables ]
            if(self.Left_turn_iterations==250):
                self.prev_Mode_LT = "Detection"
                self.Activat_LeftTurn = False
                self.Left_turn_iterations = 0
                
            self.Left_turn_iterations = self.Left_turn_iterations + 1

        # Angle of car adjusted here
        if (self.Activat_LeftTurn or self.Detected_LeftTurn):
            #Follow previously Saved Route
            self.angle = self.Frozen_Angle

    def OBEY_TrafficLights(self,Traffic_State,CloseProximity):
        # A: Car was close to TL which was signalling stop
        if((Traffic_State == "Stop") and CloseProximity):
            self.speed = 0 # Stopping car
            self.STOP_MODE_ACTIVATED = True 
        else:
            # B: Car is Nav. Traffic Light
            if (self.STOP_MODE_ACTIVATED or self.GO_MODE_ACTIVATED):
                # B-1: Car was stopped at Red and now TL has turned green
                if (self.STOP_MODE_ACTIVATED and (Traffic_State=="Go")):
                    self.STOP_MODE_ACTIVATED = False
                    self.GO_MODE_ACTIVATED = True
                # B-2: Stop Mode is activated so car cannot move
                elif(self.STOP_MODE_ACTIVATED):
                    self.speed = 0
                # B-3: Go Mode is activated --> Car moves straight ignoring lane assist
                #                               for a few moments while it crosses intersection
                elif(self.GO_MODE_ACTIVATED):
                    self.angle = 0.0
                    self.speed = 80 # Set default speed
                                        
                    if(self.crossing_intersection_timer==200):
                        self.GO_MODE_ACTIVATED = False
                        print("Intersection Crossed !!!")
                        self.crossing_intersection_timer = 0 #Reset

                    self.crossing_intersection_timer = self.crossing_intersection_timer + 1



         


class Car():

    def __init__(self):
        self.control = Control()

    def driveCar(self, frame):
        img = frame[0:640, 238:1042] # cropping of image
        # resizing to minimize computation time while still achieving
        img = cv2.resize(img,(320,240))

        img_orig = img.copy()
        cv2.imshow("Signs Localized",img_orig)
        # distance , curvature = detect_lanes(img)

        mode , tracked_class = detect_signs(img_orig, img)
        
        # current_state = [distance, curvature, img, mode , tracked_class]
        # self.control.drive(current_state)

        # # ================================= [ Display ] ============================================
        # self.display_state(img,self.control.angle,self.control.speed)
        

        # return self.control.angle, self.control.speed,  img


    def display_state(self,frame_disp,angle_of_car,current_speed,tracked_class,Traffic_State="",close_proximity=False):

        # Translate [ ROS Car Control Range ===> Real World angle and speed  ]
        angle_of_car  = interp(angle_of_car,[-0.5,0.5],[45,-45])
        if (current_speed !=0.0):
            current_speed = interp(current_speed  ,[1  ,   2],[30 ,90])

        ###################################################  Displaying CONTROL STATE ####################################

        if (angle_of_car <-10):
            direction_string="[ Left ]"
            color_direction=(120,0,255)
        elif (angle_of_car >10):
            direction_string="[ Right ]"
            color_direction=(120,0,255)
        else:
            direction_string="[ Straight ]"
            color_direction=(0,255,0)

        if(current_speed>0):
            direction_string = "Moving --> "+ direction_string
        else:
            color_direction=(0,0,255)


        cv2.putText(frame_disp,str(direction_string),(20,40),cv2.FONT_HERSHEY_DUPLEX,0.4,color_direction,1)

        angle_speed_str = "[ Angle ,Speed ] = [ " + str(int(angle_of_car)) + "deg ," + str(int(current_speed)) + "mph ]"
        cv2.putText(frame_disp,str(angle_speed_str),(20,20),cv2.FONT_HERSHEY_DUPLEX,0.4,(0,0,255),1)
        
        if (tracked_class=="left_turn"):
            font_Scale = 0.32
            if (self.Control.Detected_LeftTurn):
                tracked_class = tracked_class + " : Detected { True } "
            else:
                tracked_class = tracked_class + " : Activated { "+ str(self.Control.Activat_LeftTurn) + " } "
        else:
            font_Scale = 0.37
        cv2.putText(frame_disp,"Sign Detected ==> "+str(tracked_class),(20,80),cv2.FONT_HERSHEY_COMPLEX,font_Scale,(0,255,255),1)    

        if Traffic_State != "":
            cv2.putText(frame_disp,"Traffic Light State = [ "+Traffic_State+" ] ",(20,60),cv2.FONT_HERSHEY_COMPLEX,0.35,255)
            if close_proximity:
                cv2.putText(frame_disp," (P.Warning!) ",(220,75),cv2.FONT_HERSHEY_COMPLEX,0.35,(0,0,255))
                

