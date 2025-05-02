import Adafruit_PCA9685
import curses
import json
from time import sleep, time
import subprocess
from rpi_ws281x import *
import RPi.GPIO as GPIO
import InfraLib
import threading
import uuid
import textwrap

tests_status = {
    'servo': {
        'arm': 0,
        'front_arm': 0,
        'canon': 0
    },
    'camera': 0,
    'motor': {
        'left_motor': 0,
        'right_motor': 0
    },
    'LED': 0,
    'Infrared_LED': 0,
    'Infrared_Receiver': 0,
    'Tracking_module': 0
}

def draw_instructions(instructions_win, instructions):
    instructions_win.clear()
    instructions_win.box()
    title = "Instructions"
    max_width = instructions_win.getmaxyx()[1] - 2  # Subtract 2 for border padding
    start_x_title = max(1, (max_width - len(title)) // 2)
    instructions_win.addstr(0, start_x_title, title)

    y_position = 1  # Starting Y position for the text
    for instruction in instructions:
        wrapped_text = textwrap.wrap(instruction, max_width)
        for line in wrapped_text:
            instructions_win.addstr(y_position, 1, line)
            y_position += 1  # Move to the next line after printing

    instructions_win.refresh()

    
def draw_status(status_win):
    status_win.clear()
    status_win.box()
    title = "Status"
    start_x_title = max(1, (status_win.getmaxyx()[1] - len(title)) // 2)
    status_win.addstr(0, start_x_title, title)
    y = 1
    for test_category, tests in tests_status.items():
        
        if type(tests) == dict:
            status_win.addstr(y, 1, f"{test_category.capitalize()}")
            y += 1
            for test, status in tests.items():
                symbol = '✅' if status == 1 else ('❌' if status == -1 else ' ')
                status_win.addstr(y, 3, f"{test.capitalize()}: {symbol}")
                y += 1
        
        if type(tests) == int:
            symbol = '✅' if tests == 1 else ('❌' if tests == -1 else ' ')
            status_win.addstr(y, 1, f"{test_category.capitalize()}: {symbol}")
            y += 1
        
        y += 1
             
    status_win.refresh()
    

def testServos(instructions_win, status_win):
    
    pwm = Adafruit_PCA9685.PCA9685()
    pwm.set_pwm_freq(50)
    
    with open('servo_positions.json', 'r') as f:
        servo_info = json.load(f)
    
    with open('servoIDs.json', 'r') as f:
        servoIDs = json.load(f)
     
    draw_instructions(instructions_win,
    ["Servo Testing Phase:",
     "Each servo will move through its full range of motion.",
     "Press any key to start."]
    )
    instructions_win.getch()
    
    for servo in servo_info.keys():
        pos = servo_info.get(servo).get('default')
        pwm.set_pwm(servoIDs.get(servo), 0, pos)
        if servo != "canon_rotation":
            
            draw_instructions(instructions_win,
                [f"Testing {servo} servo"]
            )
            
            while pos < servo_info.get(servo).get('max'):
                pos += 5
                pwm.set_pwm(servoIDs.get(servo), 0, pos)
                sleep(0.05)
            while pos > servo_info.get(servo).get('min'):
                pos -= 5
                pwm.set_pwm(servoIDs.get(servo), 0, pos)
                sleep(0.05)
            while pos < servo_info.get(servo).get('default'):
                pos += 5
                pwm.set_pwm(servoIDs.get(servo), 0, pos)
                sleep(0.05)
    
            draw_instructions(instructions_win,
                [f"Testing {servo} servo",
                "Did it work? Press y/n."]
            )
            key = instructions_win.getch()
            
            if key == ord('y'):
                tests_status["servo"][servo] = 1
            elif key == ord('n'):
                   tests_status["servo"][servo] = -1
            else:
                key = instructions_win.getch()
            
            draw_status(status_win)
            
def testCamera(instructions_win, status_win):
    
    draw_instructions(instructions_win,
    ["Camera Testing Phase:",
     "The camera output will be displayed for about 3 seconds",
     "Press any key to start"]
    )
    instructions_win.getch()
    
    subprocess.run("raspistill -t 3000", shell=True)
    
    draw_instructions(instructions_win,
    ["Camera Testing Phase:",
     "Did it work? Press y/n"]
    )
    key = instructions_win.getch()
    
    if key == ord('y'):
        tests_status["camera"] = 1
    elif key == ord('n'):
        tests_status["camera"] = -1
    else:
        key = instructions_win.getch()
        
    draw_status(status_win)
    
def testMotors(instructions_win, status_win):
    
    Motor_A_EN    = 7
    Motor_B_EN    = 11

    Motor_A_Pin1  = 8
    Motor_A_Pin2  = 10
    Motor_B_Pin1  = 13
    Motor_B_Pin2  = 12
    
    Dir_forward   = 0
    Dir_backward  = 1
    
    def motorStop():
        GPIO.output(Motor_A_Pin1, GPIO.LOW)
        GPIO.output(Motor_A_Pin2, GPIO.LOW)
        GPIO.output(Motor_B_Pin1, GPIO.LOW)
        GPIO.output(Motor_B_Pin2, GPIO.LOW)
        GPIO.output(Motor_A_EN, GPIO.LOW)
        GPIO.output(Motor_B_EN, GPIO.LOW)
        
    def setup():
        global pwm_A, pwm_B
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(Motor_A_EN, GPIO.OUT)
        GPIO.setup(Motor_B_EN, GPIO.OUT)
        GPIO.setup(Motor_A_Pin1, GPIO.OUT)
        GPIO.setup(Motor_A_Pin2, GPIO.OUT)
        GPIO.setup(Motor_B_Pin1, GPIO.OUT)
        GPIO.setup(Motor_B_Pin2, GPIO.OUT)

        motorStop()
        try:
            pwm_A = GPIO.PWM(Motor_A_EN, 1000)
            pwm_B = GPIO.PWM(Motor_B_EN, 1000)
        except:
            pass
        
    def motor_left(status, direction, speed):#Motor 2 positive and negative rotation
        if status == 0: # stop
            GPIO.output(Motor_B_Pin1, GPIO.LOW)
            GPIO.output(Motor_B_Pin2, GPIO.LOW)
            GPIO.output(Motor_B_EN, GPIO.LOW)
        else:
            if direction == Dir_backward:
                GPIO.output(Motor_B_Pin1, GPIO.HIGH)
                GPIO.output(Motor_B_Pin2, GPIO.LOW)
                pwm_B.start(100)
                pwm_B.ChangeDutyCycle(speed)
            elif direction == Dir_forward:
                GPIO.output(Motor_B_Pin1, GPIO.LOW)
                GPIO.output(Motor_B_Pin2, GPIO.HIGH)
                pwm_B.start(0)
                pwm_B.ChangeDutyCycle(speed)
                
    
    def motor_right(status, direction, speed):#Motor 1 positive and negative rotation
        if status == 0: # stop
            GPIO.output(Motor_A_Pin1, GPIO.LOW)
            GPIO.output(Motor_A_Pin2, GPIO.LOW)
            GPIO.output(Motor_A_EN, GPIO.LOW)
        else:
            if direction == Dir_forward:
                GPIO.output(Motor_A_Pin1, GPIO.HIGH)
                GPIO.output(Motor_A_Pin2, GPIO.LOW)
                pwm_A.start(100)
                pwm_A.ChangeDutyCycle(speed)
            elif direction == Dir_backward:
                GPIO.output(Motor_A_Pin1, GPIO.LOW)
                GPIO.output(Motor_A_Pin2, GPIO.HIGH)
                pwm_A.start(0)
                pwm_A.ChangeDutyCycle(speed)
        return direction
    
    # Test
    setup()
    
    draw_instructions(instructions_win,
    ["Motor Testing Phase:",
     "⚠️ Please lift the robot in the air for the phase",
     "The left motor will move forward and backward",
     "Press any key to start"]
    )
    instructions_win.getch()
    
    # LEFT
    motor_left(1, 0, int(100*0.6))
    sleep(1)
    motorStop()
    motor_left(1, 1, int(100*0.6))
    sleep(1)
    motorStop()
    
    draw_instructions(instructions_win,
    ["Motor Testing Phase:",
     "Did it work? Press y/n"]
    )
    key = instructions_win.getch()
    
    if key == ord('y'):
        tests_status["motor"]["left_motor"] = 1
    elif key == ord('n'):
        tests_status["motor"]["left_motor"] = -1
    else:
        key = instructions_win.getch()
        
    draw_status(status_win)
        
    draw_instructions(instructions_win,
    ["Motor Testing Phase:",
     "⚠️ Please lift the robot in the air for the phase",
     "The right motor will move forward and backward",
     "Press any key to start"]
    )
    instructions_win.getch()
    
    # RIGHT
    motor_right(1, 0, int(100*0.6))
    sleep(1)
    motorStop()
    motor_right(1, 1, int(100*0.6))
    sleep(1)
    motorStop()
    
    GPIO.cleanup()
    
    draw_instructions(instructions_win,
    ["Motor Testing Phase:",
     "Did it work? Press y/n"]
    )
    key = instructions_win.getch()
    
    if key == ord('y'):
        tests_status["motor"]["right_motor"] = 1
    elif key == ord('n'):
        tests_status["motor"]["right_motor"] = -1
    else:
        key = instructions_win.getch()
        
    draw_status(status_win)
    
    
def testLEDs(instructions_win, status_win):
    LED_COUNT      = 16      # Number of LED pixels.
    LED_PIN        = 12      # GPIO pin connected to the pixels (18 uses PWM!).
    LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
    LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
    
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    
    def colorWipe(R, G, B):
        color = Color(R, G, B)
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, color)
            strip.show()
            
    draw_instructions(instructions_win,
    ["LED Testing Phase:",
     "The LEDs should blink in different colors for 3 seconds",
     "Press any key to start."]
    )
    instructions_win.getch()

    start_time = time()  
    while time() - start_time < 3:
        colorWipe(255, 0, 0)  # red
        sleep(0.5)
        colorWipe(0, 255, 0)  # green
        sleep(0.5)
        colorWipe(0, 0, 255)  # blue
        sleep(0.5)
    
    colorWipe(0, 0, 0)
    
    draw_instructions(instructions_win,
    ["LED Testing Phase:",
     "Did it work? Press y/n"]
    )
    key = instructions_win.getch()
    
    if key == ord('y'):
        tests_status["LED"] = 1
    elif key == ord('n'):
        tests_status["LED"] = -1
    else:
        key = instructions_win.getch()
    
    draw_status(status_win)
    
def testInfraLED(instructions_win, status_win, again=False):
    
    if not again:
        draw_instructions(instructions_win,
        ["Infrared LED Testing Phase:",
        "Point your phone's camera towards the infrared LED, you should see it blink for about 5 seconds",
        "NB: The light intensity is very low. Ensure your phone is perfectly aligned with the LED.",
        "Press any key to start."]
        )
        instructions_win.getch()
    else:
        draw_instructions(instructions_win,
        ["Infrared LED Testing Phase:",
        "Point your phone's camera towards the infrared LED, you should see it blink for about 3 seconds",
        "NB: The light intensity is very low. Ensure your phone is perfectly aligned with the LED."]
        )
    
    start_time = time()  
    while time() - start_time < 3:
        InfraLib.IRBlast(uuid.getnode(), "LASER")
        sleep(0.5)
        
    draw_instructions(instructions_win,
        ["Infrared LED Testing Phase:",
        "Did it work? Press y/n",
        "Press r to do it again",
        "Press c to continue (you migth not be able to see the light)"]
    )
    key = instructions_win.getch()
    
    if key == ord('y'):
        tests_status["Infrared_LED"] = 1
    elif key == ord('n'):
        tests_status["Infrared_LED"] = -1
    elif key == ord('r'):
        testInfraLED(instructions_win, status_win, again=True)
    elif key == ord('c'):
        pass
    else:
        key = instructions_win.getch()
    
    draw_status(status_win)
    
    
def testInfraReceiver(instructions_win, status_win):
    
    draw_instructions(instructions_win,
        ["Infrared Receiver Testing Phase:",
        "Point IR LED towards the IR receiver",
        "Press any key to start."]
    )
    instructions_win.getch()
    
    def listen_for_signal():
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        IR_RECEIVER = 15
        GPIO.setup(IR_RECEIVER, GPIO.IN)
        
        ir_receiver_working = False
        start_time = time()
        while time() - start_time < 2:
            shooter_value = InfraLib.getSignal(IR_RECEIVER)
            if shooter_value == "0xf1" + hex(uuid.getnode())[2:]:
                ir_receiver_working = True   
                break
            
        if ir_receiver_working == True:
            tests_status["Infrared_Receiver"] = 1
            draw_instructions(instructions_win,
                ["Infrared Receiver Testing Phase:",
                "It's working",
                "Press any key to continue."]
            )
        else:
            tests_status["Infrared_Receiver"] = -1
            draw_instructions(instructions_win,
                ["Infrared Receiver Testing Phase:",
                "It's not working",
                "Press any key to continue."]
            )
            
        GPIO.cleanup()
        draw_status(status_win)
        instructions_win.getch()
        
    listening_thread = threading.Thread(target=listen_for_signal)
    listening_thread.start()
    InfraLib.IRBlast(uuid.getnode(), "LASER")
    listening_thread.join()
    
    
def testTrackingModule(instructions_win, status_win):
    
    LINE_PIN_MIDDLE = 36
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LINE_PIN_MIDDLE,GPIO.IN)
    
    draw_instructions(instructions_win,
        ["Tracking Module Testing Phase:",
        "Place a black object under the robot, then press any key."]
    )
    instructions_win.getch()
    
    if GPIO.input(LINE_PIN_MIDDLE) == GPIO.HIGH:
        draw_instructions(instructions_win,
            ["Tracking Module Testing Phase:",
             "Now place a white sheet of paper under the robot, then press any key."]
        )
        instructions_win.getch()
        
        if GPIO.input(LINE_PIN_MIDDLE) == GPIO.LOW:
            draw_instructions(instructions_win,
                ["Tracking Module Testing Phase:",
                 "The module is functioning correctly.",
                 "Press any key to continue."]
            )
            tests_status["Tracking_module"] = 1
        
        else:
            draw_instructions(instructions_win,
                ["Tracking Module Testing Phase:",
                 "The module is not functioning correctly.",
                 "Press any key to continue."]
            )
            tests_status["Tracking_module"] = -1
            
        
    else:
        draw_instructions(instructions_win,
            ["Tracking Module Testing Phase:",
            "There appears to be an issue.",
            "Press any key to exit."]
        )
        tests_status["Tracking_module"] = -1
        
    draw_status(status_win)
    instructions_win.getch()

        

def main(stdscr):
    stdscr.clear()
    stdscr.refresh()
    curses.mousemask(0)

    h, w = stdscr.getmaxyx()
    instructions_win = curses.newwin(h, w // 2, 0, 0)
    status_win = curses.newwin(h, w // 2, 0, w // 2)
    
    
    draw_instructions(instructions_win,
    ["This program aims to test every functionality of the robot.",
     "Each component will be tested sequentially.",
     "Press any key to start."]
    )
    draw_status(status_win)
    instructions_win.getch()
    
    #testServos(instructions_win, status_win)
    testCamera(instructions_win, status_win)
    testMotors(instructions_win, status_win)
    testLEDs(instructions_win, status_win)
    testInfraLED(instructions_win, status_win)
    testInfraReceiver(instructions_win, status_win)
    testTrackingModule(instructions_win, status_win)
    
    sleep(0.2)

    stdscr.addstr(h - 1, 0, "Test complete. Press any key to exit.")
    stdscr.refresh()
    stdscr.getch()

if __name__ == '__main__':
    curses.wrapper(main)