from machine import I2C, Pin
from ds3231 import *
import time

sda_pin=Pin(4)
scl_pin=Pin(5)

i2c = I2C(0, scl=scl_pin, sda=sda_pin)
time.sleep(0.5)

ds = DS3231(i2c)

# Print the current date in the format: month/day/year
print( "Date={}/{}/{}" .format(ds.get_time()[1], ds.get_time()[2],ds.get_time()[0]) )

# Print the current time in the format: hours:minutes:seconds
print( "Time={}:{}:{}" .format(ds.get_time()[3], ds.get_time()[4],ds.get_time()[5]) )