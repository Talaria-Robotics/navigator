import inverse_kinematics as ik
import L2_speed_control as sc
from time import sleep
import vector as vec


# Depending on the area that the LIDAR detects obstacles, it will pivot in the opposite direction to avoid
# then it will continue moving straight. This behavior is typical of a Roomba vacuum cleaner.
def avoid_obstacles():
    pole = vec.getNearest()
    if (pole[0] < .3 and pole[1] < 0 and pole[1] > -70):
        sc.driveOpenLoop(ik.getPdTargets([-0.2, 0.5]))
        sleep(.8)
        print("Backing up")
    elif (pole[0] < .3 and pole[1] < 70 and pole[1] > 0):
        sc.driveOpenLoop(ik.getPdTargets([-0.2, -0.5]))
        sleep(.8)
        print("Backing up")
    elif (pole[0] < .25 and pole[1] > 70 or pole[1] < -70):
        sc.driveOpenLoop(ik.getPdTargets([0.4, 0]))
        sleep(.5)
        print("Dodging")
    else:
        sc.driveOpenLoop(ik.getPdTargets([0.2,0]))
        print("Roaming")

# THINGS TO DO:
# - Read in LIDAR
# - If obstacle, wait 10 seconds
    # - If the obstacle is still there
        # - If obstacle is on the left
            # - turn 90* clockwise
            # - forward 10"
            # - turn 90* counterclockwise
            # - forward 10" 
            # - turn 90* counterclockwise
            # - forward 10" 
            # - turn 90* clockwise
            # - subtract 10" from distance to travel to point
        # - If obstacle is on the right
            # - turn 90* counterclockwise
            # - forward 10"
            # - turn 90* clockwise
            # - forward 10" 
            # - turn 90* clockwise
            # - forward 10" 
            # - turn 90* counterclockwise
            # - subtract 10" from distance to travel to point
    # - If the obstacle is gone -> continue



if __name__ == "__main__":
    while (1):
       
        avoid_obstacles()
        pole = vec.getNearest()
        print(pole[0], pole[1])








        # Adjust motion based on obstacle avoidance
        velocities = avoid_obstacles(lidarData)
       
        # Calculate wheel speeds using inverse kinematics
        wheel_speeds = ik.getPdTargets(velocities)
       
        # Drive with open-loop control
        sc.driveOpenLoop(wheel_speeds)
       
        # Wait for the specified duration
        sleep(1)
