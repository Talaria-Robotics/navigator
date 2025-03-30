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

times = [row[0] / 1000 for row in data]
angleLs = [row[1] for row in data]
angleRs = [row[2] for row in data]
angleDispLs = [row[3] for row in data]
angleDispRs = [row[4] for row in data]
dThetaLs = [row[5] for row in data]
dThetaRs = [row[6] for row in data]

fig, ax = plt.subplots()
ax.plot(times, angleDispLs)
ax.plot(times, angleDispRs)
plt.show()