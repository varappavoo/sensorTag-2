# all configuration settings come from config.py
try:
	import hana_config as config
except ImportError:
	print("__HANA__: Please copy template-config.py to config.py and configure appropriately !"); exit();

debug_communication=1

import urllib3
import time
import json

import sys
import signal
import threading

class hana_uploader(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.http = self.url = self.headers = self.body = None
		self.initialized = False
		self.stop = False
		self.sensor_data = [ [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] ]
	
	def run(self):
		# disable InsecureRequestWarning if your are working without certificate verification
		# see https://urllib3.readthedocs.org/en/latest/security.html
		# be sure to use a recent enough urllib3 version if this fails
		try:
			urllib3.disable_warnings()
		except:
			print("__HANA__: urllib3.disable_warnings() failed - get a recent enough urllib3 version to avoid potential InsecureRequestWarning warnings! Can and will continue though.")

		# use with or without proxy
		if (config.proxy_url == ''):
			self.http = urllib3.PoolManager()
		else:
			self.http = urllib3.proxy_from_url(config.proxy_url)

		self.url='https://iotmms' + config.hcp_account_id + config.hcp_landscape_host + '/com.sap.iotservices.mms/v1/api/http/data/' + str(config.device_id)

		self.headers = urllib3.util.make_headers(user_agent=None)

		# use with authentication
		self.headers['Authorization'] = 'Bearer ' + config.oauth_credentials_for_device
		self.headers['Content-Type'] = 'application/json;charset=utf-8'

		print("__HANA__: Success at IoT Service Config")

		self.initialized = True

		while not self.stop:
				time.sleep(1)
				self.send_to_hcp(int(time.time()), "CC2650_01", self.sensor_data[3][0], self.sensor_data[3][1], self.sensor_data[3][2], self.sensor_data[6][0], self.sensor_data[5][0])

	def update_sensor_data(self, sensor_data):
		self.sensor_data = sensor_data

	def set_stop(self):
		self.stop = True

	def is_initialized(self):
		return self.initialized

	def send_to_hcp(self, TimeStamp, sensor_id, acc_x, acc_y, acc_z, Temp, Hum):
		body= self.create_body(TimeStamp, sensor_id, acc_x, acc_y, acc_z, Temp, Hum)
		self.upload_to_hcp(self.http, self.url, self.headers, body)
		if (debug_communication == 1):
			print("Sent to HCP")

	def upload_to_hcp(self, http, url, headers, body):
		#print(timestamp)
		#print(body)
		#print(url)
		r = http.urlopen('POST', url, body=body, headers=headers)
		if (debug_communication == 1):
			print("__HANA__: send_to_hcp():" + str(r.status))
			print(r.data)

	def create_body(self, TimeStamp, sensor_id, acc_x, acc_y, acc_z, Temp, Hum):
		body='{"mode":"async","messageType":'+ str(config.message_type_id_From_device) +',"messages":[{"Timestamp":'+ str(TimeStamp) +',"Sensor_ID":'+ str(sensor_id) +',"ACC_X":'+ str(acc_x) +',"ACC_Y":'+ str(acc_y) +',"ACC_Z":'+ str(acc_z) +',"Temperature":'+ str(Temp) +',"Humidity":'+ str(Hum) +'}]}'
		return body

	def poll_from_hcp(self, http, url, headers):
		global msg_string

		r = http.urlopen('GET', url, headers=headers)
		if (debug_communication == 1):
			print("poll_from_hcp():" + str(r.status))
			print(r.data)
		json_string='{"all_messages":'+(r.data).decode("utf-8")+'}'
		# print(json_string)

		try:
			json_string_parsed=json.loads(json_string)
			# print(json_string_parsed)
			# take care: if multiple messages arrive in 1 payload - their order is last in / first out - so we need to traverse in reverese order
			try:
				messages_reversed=reversed(json_string_parsed["all_messages"])
				for single_message in messages_reversed:
					# print(single_message)
					payload=single_message["messages"][0]
					opcode=payload["opcode"]
					operand=payload["operand"]
					# print(opcode)
					# print(operand)
					# now do things depending on the opcode
					if (opcode == "display"):
						# print(operand)
						# we write to the display at one centralized point only
						msg_string=operand
					if (opcode == "led"):
						if (operand == "0"):
							# print("LED off")
							switch_led(0)
						if (operand == "1"):
							# print("LED on")
							switch_led(1)
			except TypeError:
				print("__HANA__: Problem decoding the message " + (r.data).decode("utf-8") + " retrieved with poll_from_hcp()! Can and will continue though.")
		except ValueError:
			print("__HANA__: Problem decoding the message " + (r.data).decode("utf-8") + " retrieved with poll_from_hcp()! Can and will continue though.")
		
if __name__ == '__main__':
	hana_uploader()
	print("Done.")
