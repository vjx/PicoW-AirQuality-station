# MicroPython Library for DFRobot Oxygen Sensor
import utime
from machine import I2C, Pin

# I2C address select
ADDRESS_0 = 0x70
ADDRESS_1 = 0x71
ADDRESS_2 = 0x72
ADDRESS_3 = 0x73

# Registers
OXYGEN_DATA_REGISTER = 0x03
USER_SET_REGISTER = 0x08
AUTUAL_SET_REGISTER = 0x09
GET_KEY_REGISTER = 0x0A

class DFRobot_Oxygen:
    def __init__(self, i2c, addr=ADDRESS_0):
        self.i2c = i2c
        self.addr = addr
        self.__key = 0.0
        self.__count = 0
        self.__oxygendata = [0] * 101
        self.get_flash()

    def get_flash(self):
        try:
            rslt = self.read_reg(GET_KEY_REGISTER, 1)
            if rslt[0] == 0:
                self.__key = 20.9 / 120.0
            else:
                self.__key = float(rslt[0]) / 1000.0
            utime.sleep_ms(100)
        except Exception as e:
            print('Error getting flash:', e)

    def calibrate(self, vol, mv):
        try:
            if abs(mv) < 1e-6:
                self.write_reg(USER_SET_REGISTER, [int(vol * 10)])
            else:
                self.write_reg(AUTUAL_SET_REGISTER, [int((vol / mv) * 1000)])
        except Exception as e:
            print('Calibration error:', e)

    def get_oxygen_data(self, collect_num):
        self.get_flash()
        if collect_num <= 0 or collect_num > 100:
            return -1
        
        for num in range(collect_num - 1, 0, -1):
            self.__oxygendata[num] = self.__oxygendata[num - 1]
        
        rslt = self.read_reg(OXYGEN_DATA_REGISTER, 3)
        self.__oxygendata[0] = self.__key * (rslt[0] + rslt[1] / 10.0 + rslt[2] / 100.0)

        if self.__count < collect_num:
            self.__count += 1

        return self.get_average_num(self.__oxygendata, self.__count)

    def get_average_num(self, data, length):
        return sum(data[:length]) / length

    def write_reg(self, reg, data):
        self.i2c.writeto_mem(self.addr, reg, bytes(data))

    def read_reg(self, reg, length):
        return list(self.i2c.readfrom_mem(self.addr, reg, length))

# Example usage:
# i2c = I2C(0, scl=Pin(5), sda=Pin(4))
# sensor = DFRobot_Oxygen(i2c, addr=ADDRESS_0)
# print(sensor.get_oxygen_data(10))
