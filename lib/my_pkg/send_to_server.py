from lib.my_pkg.konstants import server_constants
import adafruit_connection_manager
import adafruit_requests
import wifi
from adafruit_datetime import datetime, date, time

def check_forwarding_server() -> any:
   try:
      # url = server_constants["json_get_particlesizecounts_Mac"]
      url = server_constants["json_get_particlesizecounts_NAS"]
      pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
      # ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
      # requests = adafruit_requests.Session(pool, ssl_context)
      requests = adafruit_requests.Session(pool)
      with requests.get(url) as response:
         r = response.json()
   except Exception as e:
      raise Exception(f"Forwarding server down? {e}")   
   return (response.status_code, response.json()['id'])

def post_to_server(data: dict) -> any:
   try:
      # url = server_constants["json_post_particlesizecounts_Mac"]
      url = server_constants["json_post_particlesizecounts_NAS"]
      DATA = data
      pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
      # ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
      # requests = adafruit_requests.Session(pool, ssl_context)
      requests = adafruit_requests.Session(pool)
      headers = {"Content-Type": "application/json"}
      with requests.post(url, json=DATA, headers=headers) as response:
         r = response.json()
         # print(f"🛀{response.json()}🛀")
   except Exception as e:
      print(f"An exception was raised in {__name__}")
      raise Exception(f"🪖 From post_to_server {e} 🪖")   
   if(response.status_code != 201):
      raise Exception(f"🪖 Status Code from forwarding server {response.status_code} 🪖")
   return (response.status_code, response.json()['id'], response.json()['firebase_id'], response.json()['forwarder'])