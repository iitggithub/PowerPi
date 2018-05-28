#!/usr/bin/python

# This script takes sensor data from sensor.py and sends
# the current value from each sensor to influxdb
# Requires pip install influxdb
from influxdb import InfluxDBClient	# used to connect to influxdb
import sensor                           # sensor data gathering script
import socket                           # used to determine host name

ac_frequency = 50                       # 50 Hz in australia
phase = 1                               # single phase voltage
#phase = 3                               # three phase voltage
i_sensor_count = 7                      # Number of current sensors attached
config = 'current.conf'                 # Configuration file for sensor boards
host     = "influxdb"
port     = "8086"
db       = "powerpi"
username = "powerpi"
password = "powerpi"

def get_voltage(data, phase=1):
	"""
	   determines the current voltage reading to use based
	   on which voltage pin the current pin is connected to.
	"""
	if phase is 1:
		return data['data'][-1]['{#SENSOR_VALUE}']
	else:
		### This needs to open the config file, figure out
		### the voltage pin and determine where it is in the
		### array and return the sensor value.
		return data['data'][-1]['{#SENSOR_VALUE}']

def power_factor(rp=0.0,ap=0.0,phase=1):
	"""
	   Calculates the power factor for an AC circuit.
	   formula's grabbed from:
	   http://www.rapidtables.com/electric/Power_Factor.htm
	"""

	# If everything is 0.0, return 0.0 to avoid division by
	# zero errors
	if 0.0 not in (rp, ap):
		return 0.0

	if phase is 3:
		# Three phase circuit
		return 1000 * rp / (3 * ap)
	else:
		# Single phase circuit
		return 1000 * rp / ap

def send(key, v, i, rp, ap, pf=0.0, f=50):
	"""
           Sends the value for a sensor (key) to influxdb
           We also need to ensure that this script runs on a regular
           basis via cron. ie:
           */15 * * * * root /usr/bin/python /usr/local/bin/influxdb.py 2>&1 >/dev/null
	"""

	client = InfluxDBClient(host, port, username, password, db)

	json_body = [
            {
                "measurement": "power",
                "sensor": key,
                "fields": {
                    "sensor": key,
                    "Voltage": v,
                    "Current": i,
                    "RealPower": rp,
                    "ApparentPower": ap,
		    "PowerFactor": pf,
		    "Frequency": f,
                }
            },
        ]

	client.write_points(json_body)

def main():
	# grab the current sensor data
	data = sensor.data(config_file=config)
	for i in range(len(data['data'])):
	
		c  = data['data'][(i + (i_sensor_count * 2))]['{#SENSOR_VALUE}']
		v  = get_voltage(data)
		rp = data['data'][i]['{#SENSOR_VALUE}']
		ap = data['data'][(i + i_sensor_count)]['{#SENSOR_VALUE}']
		pf = power_factor(rp,ap)

		send((i + 1),
                     v,
                     c,
                     rp,
                     ap,
                     pf,
                     ac_frequency)

		# We've looped through all of the sensors (minus the voltage sensors)
		if i is (i_sensor_count - phase):
			break;

# Start program
if __name__ == "__main__":
	main()
