#!/usr/bin/env python3

import os
import sys
import sqlite3
import json
import datetime
import time
import RPi.GPIO as GPIO

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

"""

model name         : ARMv6-compatible processor rev 7 (v6l)
BogoMIPS           : 997.08
Revision           : 9000c1
SoC                : BCM2835
Model              : Raspberry Pi Zero W Rev 1.1
RAM                : 512Mb
Storage            : MicroSD
USB ports          : 1 (excluding power)
Ethernet ports     : 0
Wi-fi              : True
Bluetooth          : True
Camera ports (CSI) : 1
Display ports (DSI): 0

Raspberry PI Zero W GPIO pinout header

 +-----+-----+---------+------+---+-Pi ZeroW-+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 |     |     |    3.3v |      |   |  1 || 2  |   |      | 5v      |     |     |
 |   2 |   8 |   SDA.1 |   IN | 1 |  3 || 4  |   |      | 5v      |     |     |
 |   3 |   9 |   SCL.1 |   IN | 1 |  5 || 6  |   |      | 0v      |     |     |
 |   4 |   7 | GPIO. 7 |   IN | 1 |  7 || 8  | 0 | IN   | TxD     | 15  | 14  |
 |     |     |      0v |      |   |  9 || 10 | 1 | IN   | RxD     | 16  | 15  |
 |  17 |   0 | GPIO. 0 |   IN | 0 | 11 || 12 | 0 | IN   | GPIO. 1 | 1   | 18  |
 |  27 |   2 | GPIO. 2 |   IN | 0 | 13 || 14 |   |      | 0v      |     |     |
 |  22 |   3 | GPIO. 3 |   IN | 0 | 15 || 16 | 0 | IN   | GPIO. 4 | 4   | 23  |
 |     |     |    3.3v |      |   | 17 || 18 | 0 | IN   | GPIO. 5 | 5   | 24  |
 |  10 |  12 |    MOSI | ALT0 | 0 | 19 || 20 |   |      | 0v      |     |     |
 |   9 |  13 |    MISO | ALT0 | 0 | 21 || 22 | 0 | IN   | GPIO. 6 | 6   | 25  |
 |  11 |  14 |    SCLK | ALT0 | 0 | 23 || 24 | 1 | OUT  | CE0     | 10  | 8   |
 |     |     |      0v |      |   | 25 || 26 | 1 | OUT  | CE1     | 11  | 7   |
 |   0 |  30 |   SDA.0 |   IN | 1 | 27 || 28 | 1 | IN   | SCL.0   | 31  | 1   |
 |   5 |  21 | GPIO.21 |   IN | 1 | 29 || 30 |   |      | 0v      |     |     |
 |   6 |  22 | GPIO.22 |   IN | 1 | 31 || 32 | 0 | IN   | GPIO.26 | 26  | 12  |
 |  13 |  23 | GPIO.23 |   IN | 0 | 33 || 34 |   |      | 0v      |     |     |
 |  19 |  24 | GPIO.24 |   IN | 0 | 35 || 36 | 0 | IN   | GPIO.27 | 27  | 16  |
 |  26 |  25 | GPIO.25 |   IN | 0 | 37 || 38 | 0 | IN   | GPIO.28 | 28  | 20  |
 |     |     |      0v |      |   | 39 || 40 | 0 | IN   | GPIO.29 | 29  | 21  |
 +-----+-----+---------+------+---+----++----+---+------+---------+-----+-----+
 | BCM | wPi |   Name  | Mode | V | Physical | V | Mode | Name    | wPi | BCM |
 +-----+-----+---------+------+---+-Pi ZeroW-+---+------+---------+-----+-----+


J8:
   3V3  (1) (2)  5V
 GPIO2  (3) (4)  5V
 GPIO3  (5) (6)  GND
 GPIO4  (7) (8)  GPIO14
   GND  (9) (10) GPIO15
GPIO17 (11) (12) GPIO18
GPIO27 (13) (14) GND
GPIO22 (15) (16) GPIO23
   3V3 (17) (18) GPIO24
GPIO10 (19) (20) GND
 GPIO9 (21) (22) GPIO25
GPIO11 (23) (24) GPIO8
   GND (25) (26) GPIO7
 GPIO0 (27) (28) GPIO1
 GPIO5 (29) (30) GND
 GPIO6 (31) (32) GPIO12
GPIO13 (33) (34) GND
GPIO19 (35) (36) GPIO16
GPIO26 (37) (38) GPIO20
   GND (39) (40) GPIO21


We use BCM-26 for 5Volts relay controller.

    .----------------.        .---------------------.       .-----------------------.
    |    12V DC    + |--------| NO              VCC |-------| 5V                    |
PS -|    Power       |        |                     |       |                       |
    |  Connector   - |--. .---| COM    RELAY    GND |-------| GND       RPI 0 W     |
    '----------------'  | |   |                     |       |                       |
                        | |   | NC               IN |-------| BCM 26                |
                        | |   '---------------------'       '-----------------------'
                        | |
                        | |
                 .----------------.
                 |      - +       |
                 |     12 v       |
                 |   water pump   |
                 '----------------'



MCP3008 Pinout Header

           .---o---.
           |       |
      CH0 -|   M   |- VDD
      CH1 -|   C   |- VREF
      CH2 -|   P   |- AGND
      CH3 -|   3   |- CLK
      CH4 -|   0   |- DOUT
      CH5 -|   0   |- DIN
      CH6 -|   0   |- CS/SHDN
      CH7 -|   8   |- DGND
           |       |
           '-------'


MCP3008 <=> RPI 0 W

+--------------------------------+
| MCP3008       |  RPI 0 W       |
|---------------|----------------|
| VDD           |  3.3V          |
| VREF          |  3.3V          |
| AGND          |  GND           |
| CLK           |  #11 SCLK      |
| DOUT          |  #9  MISO      |
| DIN           |  #10 MOSI      |
| CS            |  #8  CE0       |
| DGND          |  GND           |
+--------------------------------+

MCP3008 <=> Soil moisture sensor

+--------------------------------------+
| MCP3008       | Soil moisture sensor |
|---------------|----------------------|
| CH0           |  AOUT                |
+--------------------------------------+

RPI 0 W <=> Soil moisture sensor

+--------------------------------------+
| RPI 0 W       | Soil moisture sensor |
|---------------|----------------------|
| 5V            |  VCC                 |
| GND           |  GND                 |
+--------------------------------------+


# https://www.instructables.com/id/5V-Relay-Raspberry-Pi/

"""
# Bold = "\x1b[90m"
color = "\033[94m"
Reset = "\x1b[0m"

class MySqlite3Inteface:
    def __init__(self, DB_FILE="/home/pi/irrigationSystem.sqlite3"):

        createDB = not os.path.exists(DB_FILE)
        # connect to the database
        self.con = sqlite3.connect(DB_FILE)
        # instantiate a cursor obj
        self.cur = self.con.cursor()

        if createDB:
            print("Create Table")
            self.createTable()

    def createTable(self):
        irrigationTable = """
        CREATE TABLE irrigation_system (
             id integer PRIMARY KEY,
             date timestamp,
             relay_channel interger,
             moisture_sensor_channel interger,
             moisture interger,
             wateringplants integer)"""
        self.cur.execute(irrigationTable)

    def insert(self, relay_channel, moisture_sensor_channel, moisture, watering):
        sql = """INSERT INTO 'irrigation_system'
                    (date, relay_channel, moisture_sensor_channel, moisture, wateringplants)
                    VALUES (?, ?, ?, ?, ?)"""
        self.cur.execute(sql, (datetime.datetime.now(), relay_channel, moisture_sensor_channel, moisture, watering))
        self.con.commit()
        return self.cur.lastrowid

    def printAllData(self):
        self.cur.execute("SELECT id, date, relay_channel, moisture_sensor_channel, moisture, wateringplants FROM irrigation_system")
        formatted_result = [f"|{id:>8} |   {date:<28}|{relay_channel:>6}    |{moisture_sensor_channel:>10}       |{moisture:>7}   |{wateringplants:>10}          |"
                            for id, date, relay_channel, moisture_sensor_channel, moisture, wateringplants in self.cur.fetchall()]
        id, date, relay_channel, moisture_sensor_channel, moisture, wateringplants = "ID", "Date", "Relay", "Moisture Sensor", "Moisture", "Watering Plants"

        print("."+"-"*102+".")
        print('\n'.join([f"|{id:^9}|{date:^31}|{relay_channel:^10}|{moisture_sensor_channel:^17}|{moisture:^10}|{wateringplants:^20}|"] + ["|"+"-"*102+"|"] + formatted_result[-10:]))
        print("`"+"-"*102+"`")

class MyIrrigationSystem:
    def __init__(self, channelsInfo):
        # Use BCM Number
        GPIO.setmode(GPIO.BCM)

        # Hardware SPI configuration:
        SPI_PORT   = 0
        SPI_DEVICE = 0
        self.mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

        # Get the channel info for relay and the moisture sensor
        with open(channelsInfo) as fp:
            self.channelData = json.load(fp)

    def isDry(self, value):
        # Consider DRY if sensor value is > 700
        return value > 800

    def wateringPlants(self, channel):
        try:
            # Relay channel is OUTPUT
            GPIO.setup(channel["relay"], GPIO.OUT)

            # Start the motor
            GPIO.output(channel["relay"], GPIO.HIGH)  # Turn motor on
            time.sleep(10)                            # Water for 10 sec
            GPIO.output(channel["relay"], GPIO.LOW)   # Turn motor off
        except:
            print("Unexpected error:", sys.exc_info())

        finally:
            # Cleanup the GPIO
            GPIO.cleanup()

    def getMoisture(self, channel):
        # Read moisture senor value
        return self.mcp.read_adc(channel["MCP3008"])

if __name__ == "__main__":
    irrigationSystem = MyIrrigationSystem("channels.json")
    sqlite3Interface = MySqlite3Inteface()

    moistureLevel = ["Moist", "Dry"]

    for channel in irrigationSystem.channelData:
        moist = irrigationSystem.getMoisture(channel)
        watering = int(irrigationSystem.isDry(moist))
        print(color,"Relay Channel:", Reset, channel["relay"],
              color, "Moisture Sensor Channel:", Reset, channel["MCP3008"],
              color, "Moisture Level:", Reset, moist)
        print(color, "It is {}".format(moistureLevel[watering]), Reset, end = "")

        # Update Database
        sqlite3Interface.insert(channel["relay"], channel["MCP3008"], moist, watering)

        if watering:
            print("    Watering now...")
            irrigationSystem.wateringPlants(channel)
        else:
            print()

    sqlite3Interface.printAllData()
