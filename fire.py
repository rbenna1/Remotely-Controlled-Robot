import time
import uuid
from InfraLib import getSignal, IRBlast  # Make sure this is the filename where your original script is saved
import time
import RPi.GPIO as GPIO



def fireBlast():
    # Example parameters for the IRBlast function
    tank_id = uuid.getnode();
    projectile_type = "LASER"  # You can change this to another projectile type if needed
    verbose = True           # Set to True for detailed output

    # Call the IRBlast function to send the signal
    success = IRBlast(tank_id, projectile_type, verbose);
    
    if success:
        print("IR blast sent successfully!")
    else:
        print("Failed to send IR blast.")

if __name__ == "__main__":
    try : 
        fireBlast();
    except : 
        print("Failed to send IR blast.");


def ir_detection() : 
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    IR_RECEIVER = 15
    GPIO.setup(IR_RECEIVER, GPIO.IN)

   
    while True:
        received = getSignal(IR_RECEIVER)
        print(received)


        
