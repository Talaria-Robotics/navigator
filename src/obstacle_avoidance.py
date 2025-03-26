import inverse_kinematics as ik
import speed_control as sc
from time import sleep
import vector as vec
import math

wheel_radius = 0.025  # Example wheel radius in meters (5 cm)

# Function to simulate reading LIDAR data (adjust based on actual sensor)
def get_lidar_data():
    # This would typically return a list or array with obstacle data from the LIDAR sensor.
    # For now, we'll just simulate it.
    return vec.getNearest()  # Assumes vec.getNearest() returns distance and angle of the nearest object

# Function to check if the obstacle is still present after 10 seconds
def is_static_obstacle():
    print("Waiting for 10 seconds to check if the obstacle is static...")
    initial_data = get_lidar_data()
    sleep(10)  # Wait for 10 seconds to check the obstacle
    new_data = get_lidar_data()

    # Compare the two readings to check if the obstacle moved or not
    if initial_data == new_data:
        print("Obstacle is static.")
        return True
    else:
        print("Obstacle is dynamic.")
        return False

# Function to calculate the distance the robot travels based on wheel radius and time
def calculate_distance_traveled(wheel_radius, time, speed):
    """
    Calculate the distance traveled based on wheel radius, time, and speed.
    
    :param wheel_radius: Radius of the robot's wheel (meters)
    :param time: Time for which the robot moves (seconds)
    :param speed: Speed of the robot (m/s)
    :return: Distance traveled (meters)
    """
    # Distance = Speed * Time
    distance = speed * time

    # Assuming the robot is moving straight, calculate how many rotations
    # the wheels complete during this movement
    wheel_circumference = 2 * math.pi * wheel_radius  # in meters
    rotations = distance / wheel_circumference  # Number of rotations needed

    print(f"Distance traveled: {distance} meters")
    print(f"Wheel rotations: {rotations} rotations")

    return distance

# Function to avoid obstacles based on LIDAR data and static/dynamic behavior
def avoid_obstacles(wheel_radius):
    # Read the LIDAR data
    pole = get_lidar_data()

    # Check if an obstacle is detected in the front and evaluate its position
    if pole[0] < 0.3:  # If the obstacle is very close (within 30 cm)
        print("Obstacle detected!")

        # Wait 10 seconds to see if the obstacle is static or dynamic
        if is_static_obstacle():
            if pole[1] > 70 or pole[1] < -70:
                print("Obstacle is in front but not to the left or right.")
                # Move around the obstacle (assuming 10 inches is the distance to move)
                distance_to_move = 0.25  # 10 inches ≈ 0.25 meters

                # Move forward 10 inches (adjust the time and speed as per your robot's capabilities)
                sc.driveOpenLoop(ik.getPdTargets([0.4, 0]))  # Move forward
                sleep(1)  # Assuming it takes 1 second to move 0.25 meters
                calculate_distance_traveled(wheel_radius, 1, 0.4)  # Calculate distance based on time and speed

                # Turn 90° clockwise
                sc.driveOpenLoop(ik.getPdTargets([0, 0.4]))  # Turn 90° clockwise
                sleep(1)
                # Move forward another 10 inches
                sc.driveOpenLoop(ik.getPdTargets([0.4, 0]))  # Move forward
                sleep(1)
                calculate_distance_traveled(wheel_radius, 1, 0.4)  # Calculate distance traveled

                # Turn 90° counterclockwise
                sc.driveOpenLoop(ik.getPdTargets([0, -0.4]))  # Turn 90° counterclockwise
                sleep(1)

                # Move forward another 10 inches
                sc.driveOpenLoop(ik.getPdTargets([0.4, 0]))  # Move forward
                sleep(1)
                calculate_distance_traveled(wheel_radius, 1, 0.4)  # Calculate distance traveled

                # Adjust the distance by subtracting 10" from the remaining distance
                print("Obstacle avoided, returning to path.")

            elif pole[1] < 70 and pole[1] > 0:  # Obstacle is on the right side
                print("Obstacle is on the right.")
                # Move around the obstacle (move left, then back)
                distance_to_move = 0.25  # 10 inches ≈ 0.25 meters

                # Move to the left and avoid the obstacle (performing left turn and forward motion)
                sc.driveOpenLoop(ik.getPdTargets([0, -0.4]))  # Turn 90° counterclockwise
                sleep(1)
                sc.driveOpenLoop(ik.getPdTargets([0.4, 0]))  # Move forward
                sleep(1)
                calculate_distance_traveled(wheel_radius, 1, 0.4)

                # Move forward again after avoiding the obstacle
                sc.driveOpenLoop(ik.getPdTargets([0, 0.4]))  # Turn 90° clockwise
                sleep(1)
                sc.driveOpenLoop(ik.getPdTargets([0.4, 0]))  # Move forward
                sleep(1)
                calculate_distance_traveled(wheel_radius, 1, 0.4)

                # Adjust the distance by subtracting 10" from the remaining distance
                print("Obstacle on right avoided, returning to path.")

            elif pole[1] > -70 and pole[1] < 0:  # Obstacle is on the left side
                print("Obstacle is on the left.")
                # Move around the obstacle (move right, then back)
                distance_to_move = 0.25  # 10 inches ≈ 0.25 meters

                # Move to the right and avoid the obstacle (performing right turn and forward motion)
                sc.driveOpenLoop(ik.getPdTargets([0, 0.4]))  # Turn 90° clockwise
                sleep(1)
                sc.driveOpenLoop(ik.getPdTargets([0.4, 0]))  # Move forward
                sleep(1)
                calculate_distance_traveled(wheel_radius, 1, 0.4)

                # Move forward again after avoiding the obstacle
                sc.driveOpenLoop(ik.getPdTargets([0, -0.4]))  # Turn 90° counterclockwise
                sleep(1)
                sc.driveOpenLoop(ik.getPdTargets([0.4, 0]))  # Move forward
                sleep(1)
                calculate_distance_traveled(wheel_radius, 1, 0.4)

                # Adjust the distance by subtracting 10" from the remaining distance
                print("Obstacle on left avoided, returning to path.")
        else:
            print("Obstacle is dynamic or not present anymore, continuing path.")
            sc.driveOpenLoop(ik.getPdTargets([0.2, 0]))  # Continue moving forward

    else:
        print("No obstacles detected, continuing to roam.")
        sc.driveOpenLoop(ik.getPdTargets([0.2, 0]))  # Continue moving forward

def navigate():
    avoid_obstacles(wheel_radius)  # Run the obstacle avoidance function
    sleep(1)  # Delay for a bit to allow the robot to process

if __name__ == "__main__":
    while True:
        navigate()
