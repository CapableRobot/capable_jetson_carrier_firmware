from machine import Pin

## We need these pins to be set high to keep SOM power 
## on during MCU reset, after MCU has power cycled the SOM.
SOM_POWER_ENABLE = Pin(10, Pin.OUT, value=1)
EN_BUFFER = Pin(18, Pin.OUT, value=1)