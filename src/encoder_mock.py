import time
from numpy import deg2rad, mod

# Addresses (A1 pin on RIGHT pulled high)
encL = 0x40
encR = 0x41

encoders = {
    encL: 0.0,
    encR: 0.0,
}

def setMockReading(encoderSelection: int, value: float):
    encoders[encoderSelection] = mod(value, 360.0)

def singleReading(encoderSelection) -> float:
    """Takes a single angle reading in degrees"""
    try:
        degreesAngle = round(encoders[encoderSelection], 1)
    except:
        print("Encoder reading failed.")
        degreesAngle = 0
    return degreesAngle

def readShaftPositions() -> tuple[float, float]:
    """Take readings from both encoders"""
    try:
        # Left side needs to be inverted
        rawAngle = singleReading(encL)
        angleL = 360.0 - rawAngle
        angleL = round(angleL, 1)
    except:
        print('Warning(I2C): Could not read left encoder')
        angleL = 0
    
    try:
        angleR = singleReading(encR)
    except:
        print('Warning(I2C): Could not read right encoder')
        angleR = 0
    
    return (angleL, angleR)

def readShaftPositionsRad() -> tuple[float, float]:
    angleLDeg, angleRDeg = readShaftPositions()
    return (deg2rad(angleLDeg), deg2rad(angleRDeg))


if __name__ == "__main__":
    print("Testing Encoders")
    while True:
      encL_val, encR_val = readShaftPositions()
      
      print(f"Left: {encL_val}\tRight: {encR_val}")

      time.sleep(0.1)
