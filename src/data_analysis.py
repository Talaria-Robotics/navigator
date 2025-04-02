import matplotlib.pyplot as plt 
import numpy as np
import os

fileName = os.path.join("logs", "j1_to_j2.csv")

data: list[tuple[float, float, float, float, float, float, float]] = []

# Parse CSV
with open(fileName, "r") as file:
    line = file.readline()

    while len(line) > 0:
        try:
            line = file.readline()
            row = [float(d) for d in line.split(",")]
            data.append(row)
        except:
            pass

times = [row[0] for row in data]
angleLs = [np.rad2deg(row[1]) for row in data]
angleRs = [np.rad2deg(row[2]) for row in data]
angleDispLs = [row[3] for row in data]
angleDispRs = [row[4] for row in data]
dThetaLs = [row[5] for row in data]
dThetaRs = [row[6] for row in data]

def computeDisplacement(angles: list[float]) -> list[float]:
    disps = [0]
    cummulativeDisp = 0
    for i in range(1, len(angles)):
        currentAngle = angles[i]
        previousAngle = angles[i - 1]
        
        dThetaL = currentAngle - previousAngle
        if dThetaL < 0:
            dThetaL = currentAngle + (360.0 - previousAngle)
        cummulativeDisp += dThetaL

        disps.append(cummulativeDisp)
    return disps

newDispLs = computeDisplacement(angleLs)
newDispRs = computeDisplacement(angleRs)

fig, ax = plt.subplots()
ax.set_xlabel("Reading")

ax.plot(times, angleLs)
ax.plot(times, angleRs)
#ax.set_ylabel("Angular displacement")
#ax.plot(times, newDispLs)
#ax.plot(times, newDispRs)
plt.show()