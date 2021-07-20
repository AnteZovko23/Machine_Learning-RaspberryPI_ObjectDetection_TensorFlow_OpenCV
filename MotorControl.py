import RPi.GPIO as GPIO
import time
from pynput.keyboard import Key, Listener
import ObjectDetection
import threading
import pyautogui


# from getkey import getkey, keys




SERVO_IN = 29

ECHO = 31
TRIGGER = 32

ENA_TURN = 36
IN1_TURN = 38
IN2_TURN = 40

ENB_CAM = 33


IN1_CAM = 35

IN2_CAM = 37




ENA_FRONT = 3
IN1_FRONT = 5
IN2_FRONT = 7

ENB_BACK = 11
IN1_BACK = 13
IN2_BACK = 15


FREQ_SERVO = 200
cycle_SERVO = 10

FREQ_FRONT_BACK = 120
cycle_FRONT_BACK = 45

FREQ_TURN = 100
cycle_TURN = 50

FREQ_CAM = 100
cycle_CAM = 20

GPIO.setmode(GPIO.BOARD)
GPIO.setup(ENA_FRONT, GPIO.OUT)
GPIO.setup(IN1_FRONT, GPIO.OUT)
GPIO.setup(IN2_FRONT, GPIO.OUT)

GPIO.setup(ENB_BACK, GPIO.OUT)
GPIO.setup(IN1_BACK, GPIO.OUT)
GPIO.setup(IN2_BACK, GPIO.OUT)

GPIO.setup(ENA_TURN, GPIO.OUT)
GPIO.setup(IN1_TURN, GPIO.OUT)
GPIO.setup(IN2_TURN, GPIO.OUT)

GPIO.setup(ENB_CAM, GPIO.OUT)
GPIO.setup(IN1_CAM, GPIO.OUT)
GPIO.setup(IN2_CAM, GPIO.OUT)

GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(TRIGGER, GPIO.OUT)

GPIO.setup(SERVO_IN, GPIO.OUT)

GPIO.output(IN1_FRONT, GPIO.LOW)
GPIO.output(IN2_FRONT, GPIO.LOW)
GPIO.output(IN1_BACK, GPIO.LOW)
GPIO.output(IN2_BACK, GPIO.LOW)
GPIO.output(IN1_TURN, GPIO.LOW)
GPIO.output(IN2_TURN, GPIO.LOW)
GPIO.output(IN1_CAM, GPIO.LOW)
GPIO.output(IN2_CAM, GPIO.LOW)

PWM_FRONT = GPIO.PWM(ENA_FRONT, FREQ_FRONT_BACK)
PWM_TURN = GPIO.PWM(ENA_TURN, FREQ_TURN)
PWM_BACK = GPIO.PWM(ENB_BACK, FREQ_FRONT_BACK)
PWM_CAM = GPIO.PWM(ENB_CAM, FREQ_CAM)

PWM_SERVO = GPIO.PWM(SERVO_IN, FREQ_SERVO)


PWM_FRONT.start(cycle_FRONT_BACK)
PWM_BACK.start(cycle_FRONT_BACK)
PWM_TURN.start(cycle_TURN)
PWM_CAM.start(cycle_CAM)
PWM_SERVO.start(cycle_SERVO)

movingForward = False

print('\n')
print("Starting low and forward...")
print('\n')

def getDistance():
   
    start = 0
    end = 0
    GPIO.output(TRIGGER, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIGGER, GPIO.LOW)
    while GPIO.input(ECHO) == GPIO.LOW:
        start = time.time()
    

    while GPIO.input(ECHO) == GPIO.HIGH:
        end = time.time()
        


    ElapsedTime = end - start

    distance = 17150 * ElapsedTime
    time.sleep(0.2)
    return distance

def onPress(key):
    
    global cycle_FRONT_BACK
    global cycle_TURN
    global cycle_CAM
    global cycle_SERVO

    global PWM_FRONT
    global PWM_BACK
    global PWM_TURN
    global PWM_CAM

    global PWM_SERVO
    
    global movingForward

    try:
        if key.char == 'q':
            GPIO.output(IN1_TURN, GPIO.LOW)
            GPIO.output(IN2_TURN, GPIO.LOW)
            GPIO.output(IN1_FRONT, GPIO.LOW)
            GPIO.output(IN2_FRONT, GPIO.LOW)
            GPIO.output(IN1_BACK, GPIO.LOW)
            GPIO.output(IN2_BACK, GPIO.LOW)
            GPIO.output(IN1_CAM, GPIO.LOW)
            GPIO.output(IN2_CAM, GPIO.LOW)
            quit(0)

        elif key.char == 'f':
            GPIO.output(IN1_FRONT, GPIO.HIGH)
            GPIO.output(IN1_BACK, GPIO.LOW)

            GPIO.output(IN2_FRONT, GPIO.LOW)
            GPIO.output(IN2_BACK, GPIO.HIGH)
            
            movingForward = True

        elif key.char == 'r':
            GPIO.output(IN1_FRONT, GPIO.LOW)
            GPIO.output(IN1_BACK, GPIO.HIGH)
            
            GPIO.output(IN2_FRONT, GPIO.HIGH)
            GPIO.output(IN2_BACK, GPIO.LOW)
        
        elif key.char == 'a':
            if cycle_SERVO + 1 > 50:
                cycle_SERVO = 50
            else:
                cycle_SERVO += 1
            print("CAM: {}".format(cycle_SERVO))
            PWM_SERVO.ChangeDutyCycle(cycle_SERVO)
            
        
        elif key.char == 'd':
            distance = getDistance()
            distance = round(distance, 4)
            print("Distance: {} cm".format(distance))
    


        elif key.char == 's':
            if cycle_SERVO - 1 < 0:
                cycle_SERVO = 0
            else:
                cycle_SERVO -= 1
            
            print("CAM: {}".format(cycle_SERVO))
            PWM_SERVO.ChangeDutyCycle(cycle_SERVO)



    except AttributeError:
        pass

    if key == Key.up:
        if cycle_FRONT_BACK + 1 > 100:
            cycle_FRONT_BACK = 100
        else:
            cycle_FRONT_BACK += 1
        print(cycle_FRONT_BACK)
        
        PWM_FRONT.ChangeDutyCycle(cycle_FRONT_BACK)
        PWM_BACK.ChangeDutyCycle(cycle_FRONT_BACK)

    elif key == Key.down:
        if cycle_FRONT_BACK - 1 < 0:
            cycle_FRONT_BACK = 0
        else:
            cycle_FRONT_BACK -= 1

        print(cycle_FRONT_BACK)
        PWM_FRONT.ChangeDutyCycle(cycle_FRONT_BACK)
        PWM_BACK.ChangeDutyCycle(cycle_FRONT_BACK)
        
    elif key == Key.left:
        GPIO.output(IN1_TURN, GPIO.LOW)
        GPIO.output(IN2_TURN, GPIO.HIGH)

    elif key == Key.right:
        GPIO.output(IN1_TURN, GPIO.HIGH)
        GPIO.output(IN2_TURN, GPIO.LOW)


def onRelease(key):
    
    if key == Key.left or key == Key.right:
        GPIO.output(IN1_TURN, GPIO.LOW)
        GPIO.output(IN2_TURN, GPIO.LOW)
    
    try:
        if key.char == 'a' or key.char == 's':
            PWM_SERVO.ChangeDutyCycle(0)
    except AttributeError:
        pass

import time
def detectionThread():
    global cycle_FRONT_BACK
    global IN1_FRONT
    global IN2_BACK
    global movingForward
    while True:
        detection = ObjectDetection.getDetection()

        if detection != None:
            print(len(detection))
            print(detection[13])
            if detection[13] == 'R':
                if  cycle_FRONT_BACK < 75:
                    pyautogui.press('up')
            else:
                if not movingForward:
                    pyautogui.press('f')
            time.sleep(0.5)



threading.Thread(target=detectionThread, args=()).start()
with Listener(on_press = onPress, on_release = onRelease) as listener:
    #threading.Thread(target=p, args=()).start()

    ObjectDetection.detect()
    listener.join()

    
"""
while(1):
    key = getkey()

    if key == keys.UP:
        if cycle + 1 > 100:
            cycle = 100
        else:
            cycle += 1
        print(cycle)
        PWM_FRONT.ChangeDutyCycle(cycle)
        PWM_BACK.ChangeDutyCycle(cycle)
    
    elif key == keys.DOWN:
        if cycle - 1 < 0:
            cycle = 0
        else:
            cycle -= 1
        print(cycle)
        PWM_FRONT.ChangeDutyCycle(cycle)
        PWM_BACK.ChangeDutyCycle(cycle)

    elif key == 'f':
        GPIO.output(IN1_FRONT, GPIO.HIGH)
        GPIO.output(IN1_BACK, GPIO.LOW)

        GPIO.output(IN2_FRONT, GPIO.LOW)
        GPIO.output(IN2_BACK, GPIO.HIGH)
        
    elif key == 'r':
        GPIO.output(IN1_FRONT, GPIO.LOW)
        GPIO.output(IN1_BACK, GPIO.HIGH)

        GPIO.output(IN2_FRONT, GPIO.HIGH)
        GPIO.output(IN2_BACK, GPIO.LOW)


    elif key == 'b':
        GPIO.output(IN2_FRONT, GPIO.LOW)
        GPIO.output(IN1_FRONT, GPIO.LOW) 
        GPIO.output(IN1_BACK, GPIO.LOW)
        GPIO.output(IN2_BACK, GPIO.LOW)
        break
"""           



        
