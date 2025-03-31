import smbus2
import time
from numpy import deg2rad

# I2C bus
bus = smbus2.SMBus(1)

# Addresses (A1 pin on RIGHT pulled high)
encL = 0x40
encR = 0x41

def singleReading(encoderSelection) -> float:
    """Takes a single angle reading in degrees"""
    try:
        # Read ADC data from registers (14-bit value, bits 6 and 7 unused)
        twoByteReading = bus.read_i2c_block_data(encoderSelection, 0xFE, 2)
        binaryPosition = (twoByteReading[0] << 6) | (twoByteReading[1])
        
        # Convert ADC reading to degrees with 0.1 precision
        degreesPosition = binaryPosition * (360/2**14)
        degreesAngle = round(degreesPosition, 1)
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

    _, previousAngle = readShaftPositions()
    while True:
        cummulativeDisp = 0
        _, currentAngle = readShaftPositions()

        dThetaL = currentAngle - previousAngle
        if dThetaL < 0:
            dThetaL = currentAngle + (360.0 - previousAngle)
        cummulativeDisp += dThetaL

        print("{cummulativeDisp:3f}")

        time.sleep(0.25)
