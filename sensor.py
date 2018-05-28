#!/usr/bin/python

# This script is used to connect to a lechacal sensor board
# and returns the values of each sensor.

import serial      # used to connect to the serial device
import json        # used to output sensor data in json format
import argparse    # Command line argument parser

def get_args():
	"""
	   Supports the command-line arguments listed below.
	"""

	parser = argparse.ArgumentParser( \
            'Process args for retreiving stastics from Raspberry Pi ADC board')
	parser.add_argument('-p', '--port', default="/dev/ttyS0", \
            action='store', help='Serial Port to use ie /dev/ttyS0')
	parser.add_argument('-b', '--baud-rate', type=int, default=38400,
            action='store', help='Serial port baud rate to use')
	parser.add_argument('-t', '--timeout', type=int, default=3, \
            action='store', help='Timeout for serial port connection')
	parser.add_argument('-c', '--config-file', required=False, action='store', \
            help='Config File used to configure the ADC. Used to help \
            understand what kind of sensors are connected to each channel.')

	args = parser.parse_args()

	return args

def power_factor(rp,ap):
	"""
	   Calculates the power factor for an AC circuit.
	"""
	return rp / ap

def normalise_value(v):
	"""
           Anything less than 100 milliamps is probably
           ghost amperage... if that's even a thing.
           While we're at it, strip slashes too.
        """
	if float(v) < 100:
		return 0.0
	return float(v.strip())

def open_serial_port(port,
                     baud_rate,
                     to):
	"""
           Opens a connection to the serial port and return the resource.
        """

	# Open the device
	s = serial.Serial(port,
                          baud_rate,
                          timeout=to)

	# Serial port should have been opened above
	# but we'll doublecheck it.
	if(s.isOpen() == False):
		s.open()

	return s
	
def is_float(z):
	"""
            Check if z[0] is a float.
            That usually means the board is working.
	"""

	try:
		float(z[0])
		return True
	except:
		return False

def convert_sensor_type(v):
	"""
           converts the sensor type value into something
           more meaningful.
        """

	if v is 0:
		return "None"
	elif v is 1:
		return "RealPower"
	elif v is 2:
		return "ApparentPower"
	elif v is 3:
		return "Voltage"
	elif v is 4:
		return "Current"
	else:
		return "Unknown"

def get_sensor_type(channel, config_file=None):
	"""
           looks at a given configuration for channel information
           and the last line is usually the channel type.
        """

	if config_file is None:
		return "Unknown"

	a = []
	search_string = "addchannel"

	try:
		with open(config_file, 'r') as f:
			for line in f:
				if line.startswith(search_string):
					a.append(line)

		v = a[channel].split(" ")
		return convert_sensor_type(int(v[2]))
	except:
		return "Unknown"

def data(port=None,
         baud_rate=None,
         timeout=None,
         config_file=None):
	"""
           Connect to the serial port and dump the values for each sensor.
        """

	args = get_args() # Load our command line arguments

	if port is None:
		port = args.port
	if baud_rate is None:
		baud_rate = args.baud_rate
	if timeout is None:
		timeout = args.timeout
	if config_file is None:
		config_file = args.config_file

	try:
		# Open the serial port
		s = open_serial_port(port,
                                     baud_rate,
                                     timeout)

		# The first line is usually garbage so we'll 
        	# read it to get rid of it and get to the good stuff
		response = s.readline()

		while True:
			response = s.readline()

			# Assume we're outputting in CSV format so split
			# the line based on commas.
        	        z = response.split(",")

			# Check the line output. Should be an array of
			# float values.
			if is_float(z) == False:
				print response
				break

			# loop through each of the sensors and normalise the values
			sensor_array = []
			for i in range(len(z)):

				# normalise? value and strip whitespace
				v = normalise_value(z[i])

				# If we have a config file, open it and try to determine
				# the type of sensor being used.
				if config_file:
					sensor_type = get_sensor_type(i, config_file)
				else:
					sensor_type = "Unknown"

				sensor_array.append({"{#SENSOR_ID}": str(i+1),
                                                     "{#SENSOR_TYPE}": sensor_type,
                                                     "{#SENSOR_VALUE}": str(v)})

			# We're done reading the line
			break

		s.close()
		data = {"data": sensor_array}
		return data
	except KeyboardInterrupt:
		print "Error"
		s.close()

def main():
	"""
           Start the sensor data script and dump the json data
        """
	print json.dumps(data(), sort_keys=True, indent=2)

# Start program
if __name__ == "__main__":
	main()
