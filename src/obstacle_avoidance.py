import math
import time
import lidar as ld


scan_data = ld()

# Creating the "Box of View"
box = []
for x in range(0,58):
    value = 15/math.cos(x)
    box.append(value)
for x in range(59,89):
    value = 24/(math.cos(90-x))
    box.append(value)

box.append(24)

for x in range(91,147):
    value = 24/(math.cos(x-90))
    box.append(value)
for x in range(148,180):
    value = 15/(math.cas(180-x))
    box.append(value)

print("List of Distances inside Box: ", box)

"""
# Can adjust the target zone as desired
focus_zone_right = scan_data[0:90]
focus_zone_left = scan_data[269:359]

# Initializing counters for how many points have obstacles
r_counter = 0
l_counter  = 0

# Initializing counters for an obstacle detected
r_obstacle = 0
l_obstacle = 0

# -------------------------------------------------------------------------------------------------------------------
# Check the distances on the right side if there is an obstacle -------------> MAY NEED TO ADJUST THE OBSTACLE RANGE!
for x in range(len(focus_zone_right)):
    
    # Check for obstacles on RIGHT side
    if((focus_zone_right[x] >= 10) or (focus_zone_right[x] <= 500)):
        r_counter += 1

    # Check for obstacles on LEFT side
    if((focus_zone_left[x] >= 10) or (focus_zone_left[x] <= 500)):
        l_counter += 1

# -------------------------------------------------------------------------------------------------------------------
# There is a DYNAMIC obstacle
if(((r_counter > 10) or (l_counter > 10)) and ((r_obstacle == 0) or (l_obstacle == 0))):
    if((r_counter > 10)):
        print("Obstacle on RIGHT side!")
        r_obstacle = 1

    if((l_counter > 10)):
        print("Obstacle on LEFT side!")
        l_obstacle = 1
    
    # Wait to see if the obstacle moves (DYNAMIC OBSTACLE)
    time.sleep(10)

# -------------------------------------------------------------------------------------------------------------------
# There is a STATIC obstacle
if(((r_counter > 10) or (l_counter > 10)) and ((r_obstacle == 1) or (l_obstacle == 1))):
    if((r_counter > 10)):
        print("Obstacle on RIGHT side!")
        r_obstacle = 1

    if((l_counter > 10)):
        print("Obstacle on LEFT side!")
        l_obstacle = 1
    
    # Will need to move accordingly... TBD...
"""