# RaspberryPi
## My Raspberry Pi Projects

### Pi-Hole 
This is the list I am using in my pi-hole to block ads.

### Irrigation system using Raspberry Pi Zero W
I am using a capacitive soil moisture sensor to measure the soil moisture level and 5V relay to operate the water pump. The soil moisture sensor reads value between 0-1023, 0 as WATER, and 1023 as DRY. I water the plant if the soil moisture sensor value is more than 800.

The channel values (MCP3008 channel for soil moisture sensor, and BCM board pin # for the relay) are read from the input JSON file.
We can configure the json for more than one (soil moisture sensor & 5V Relay) pairs.
