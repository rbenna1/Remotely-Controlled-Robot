#!/usr/bin/env python3
# File name   : move.py
# Description : Control Motor
# Product     : GWR
# Website     : www.gewbot.com
# Author      : William
# Date        : 2019/07/24
import time
import RPi.GPIO as GPIO

# motor_EN_A: Pin7  |  motor_EN_B: Pin11
# motor_A:  Pin8,Pin10    |  motor_B: Pin13,Pin12

Motor_A_EN    = 7
Motor_B_EN    = 11

Motor_A_Pin1  = 8
Motor_A_Pin2  = 10
Motor_B_Pin1  = 13
Motor_B_Pin2  = 12

Dir_forward   = 0
Dir_backward  = 1

left_forward  = 0
left_backward = 1

right_forward = 0
right_backward= 1

pwn_A = 0
pwm_B = 0


def motorStop():#Motor stops
	GPIO.output(Motor_A_Pin1, GPIO.LOW)
	GPIO.output(Motor_A_Pin2, GPIO.LOW)
	GPIO.output(Motor_B_Pin1, GPIO.LOW)
	GPIO.output(Motor_B_Pin2, GPIO.LOW)
	GPIO.output(Motor_A_EN, GPIO.LOW)
	GPIO.output(Motor_B_EN, GPIO.LOW)


# def setup():#Motor initialization
# 	global pwm_A, pwm_B
# 	print("entering setup")
# 	GPIO.setwarnings(False)
# 	GPIO.setmode(GPIO.BOARD)
# 	print("setmode called")
# 	GPIO.setup(Motor_A_EN, GPIO.OUT)
# 	GPIO.setup(Motor_B_EN, GPIO.OUT)
# 	GPIO.setup(Motor_A_Pin1, GPIO.OUT)
# 	GPIO.setup(Motor_A_Pin2, GPIO.OUT)
# 	GPIO.setup(Motor_B_Pin1, GPIO.OUT)
# 	GPIO.setup(Motor_B_Pin2, GPIO.OUT)
# 	print("exiting setup ()")

# 	motorStop()
# 	try:
# 		pwm_A = GPIO.PWM(Motor_A_EN, 1000)
# 		pwm_B = GPIO.PWM(Motor_B_EN, 1000)
# 	except:
# 		pass

def setup():#Motor initialization
    global pwm_A, pwm_B
    print("[Move Debug] Entering move.setup()") # Modified print
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    print("[Move Debug] setmode(BOARD) called") # Modified print

    try:
        print(f"[Move Debug] About to setup Pin {Motor_A_EN} (Motor_A_EN)")
        GPIO.setup(Motor_A_EN, GPIO.OUT)
        print(f"[Move Debug] Pin {Motor_A_EN} setup OK")

        print(f"[Move Debug] About to setup Pin {Motor_B_EN} (Motor_B_EN)")
        GPIO.setup(Motor_B_EN, GPIO.OUT)
        print(f"[Move Debug] Pin {Motor_B_EN} setup OK")

        print(f"[Move Debug] About to setup Pin {Motor_A_Pin1} (Motor_A_Pin1)")
        GPIO.setup(Motor_A_Pin1, GPIO.OUT)
        print(f"[Move Debug] Pin {Motor_A_Pin1} setup OK")

        print(f"[Move Debug] About to setup Pin {Motor_A_Pin2} (Motor_A_Pin2)")
        GPIO.setup(Motor_A_Pin2, GPIO.OUT)
        print(f"[Move Debug] Pin {Motor_A_Pin2} setup OK")

        print(f"[Move Debug] About to setup Pin {Motor_B_Pin1} (Motor_B_Pin1)")
        GPIO.setup(Motor_B_Pin1, GPIO.OUT)
        print(f"[Move Debug] Pin {Motor_B_Pin1} setup OK")

        print(f"[Move Debug] About to setup Pin {Motor_B_Pin2} (Motor_B_Pin2)")
        GPIO.setup(Motor_B_Pin2, GPIO.OUT)
        print(f"[Move Debug] Pin {Motor_B_Pin2} setup OK")

    except Exception as setup_err:
        print(f"[Move Debug] !!!!! ERROR during GPIO.setup: {setup_err} !!!!!")
        # It's useful to re-raise the error so server.py catches it
        raise

    print("[Move Debug] All basic GPIO setups completed.") # Modified print

    motorStop()
    print("[Move Debug] motorStop() called after setup.")

    try:
        print("[Move Debug] About to setup PWM A")
        pwm_A = GPIO.PWM(Motor_A_EN, 1000)
        print("[Move Debug] PWM A setup OK")
        print("[Move Debug] About to setup PWM B")
        pwm_B = GPIO.PWM(Motor_B_EN, 1000)
        print("[Move Debug] PWM B setup OK")
    except Exception as pwm_err:
        print(f"[Move Debug] !!!!! ERROR during PWM setup: {pwm_err} !!!!!")
        # Decide if you need to raise here too
        # raise

    print("[Move Debug] Exiting move.setup()") # Modified print


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
		if direction == Dir_forward:#
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


def move(speed=60, direction='forward', turn='no', radius=0.6):   # 0 < radius <= 1  
	#speed = 100
	if direction == 'forward':
		if turn == 'right':
			motor_left(0, left_forward, int(speed*radius))
			motor_right(1, right_backward, speed)
		elif turn == 'left':
			motor_left(1, left_backward, speed)
			motor_right(0, right_forward, int(speed*radius))
		else:
			motor_left(1, left_backward, speed)
			motor_right(1, right_backward, speed)
	elif direction == 'backward':			
		if turn == 'right':
			motor_left(0, left_backward, int(speed*radius))
			motor_right(1, right_forward, speed)
		elif turn == 'left':
			motor_left(1, left_forward, speed)
			motor_right(0, right_backward, int(speed*radius))
		else:
			motor_left(1, left_forward, speed)
			motor_right(1, right_forward, speed)
	elif direction == 'no':
		if turn == 'right':
			motor_left(1, left_backward, speed)
			motor_right(1, right_forward, speed)
		elif turn == 'left':
			motor_left(1, left_forward, speed)
			motor_right(1, right_backward, speed)
		else:
			motorStop()
	else:
		pass


def destroy():
	motorStop()
	GPIO.cleanup()             # Release resource


if __name__ == '__main__':
	try:
		speed_set = 60
		setup()
		move(speed_set, 'forward', 'no', 0.8)
		time.sleep(1.3)
		motorStop()
		destroy()
	except KeyboardInterrupt:
		destroy()
