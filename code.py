from lib.my_pkg.set_ntp_time import set_ntp_time_is_successful, pretty_time
from lib.my_pkg.creds import creds
from lib.my_pkg.konstants import rotary_encoder_constants
from lib.my_pkg.send_to_server import check_forwarding_server
from lib.my_pkg.write_to_display import report_seconds, report_resets  
from lib.my_pkg.write_to_display import print_to_display, report
from lib.my_pkg.konstants import number_of_samples_per_minute
import board
import time
import wifi
import busio
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel
from rainbowio import colorwheel
from i2cdisplaybus import I2CDisplayBus
import displayio
from adafruit_displayio_sh1107 import SH1107, DISPLAY_OFFSET_ADAFRUIT_128x128_OLED_5297
from adafruit_pm25.i2c import PM25_I2C         # for PMSA003I PM2.5 sensor

reset_pin = None

displayio.release_displays()
# set up an I2C bus using GP27 (Yellow) as clk and GP26 (blue) as data 
i2c_bus = busio.I2C(board.GP27, board.GP26, frequency=100000) 
i2c_bus.unlock()
display_bus = I2CDisplayBus(i2c_bus, device_address=0x3D)
display = SH1107(
    display_bus,
    width=128,
    height=128,
    display_offset=DISPLAY_OFFSET_ADAFRUIT_128x128_OLED_5297,
    rotation=270,
)
print_to_display(display, i2c_bus, 1, 1)

try:
   wifi.radio.connect(creds['ssid'], creds['password'])   # connect to wifi
   print_to_display(display, i2c_bus, 2, 5)
except Exception as e:
   print_to_display(display, i2c_bus, 3, 5)
   print(f"Errored out trying to establish wifi:\n{e}\nWill not proceed further with script...")
   while True:   # do nothing forever
      pass           
    
if set_ntp_time_is_successful(wifi.radio):    # function calls ntp server to set Pico 2 W real time clock
   print_to_display(display, i2c_bus, 4, 5)
   print(f"Set real-time clock to ntp time: {pretty_time(time.localtime())}")
else:
   print_to_display(display, i2c_bus, 5, 6)
   print(f"Couldn't set real-time clock to ntp time. Continuing anyway with time reading \n{pretty_time(time.localtime())}.")

print_to_display(display, i2c_bus, 6, 5)
# # only using rotary encoders to get measurements (last rotary encoder) 
# and air quality baseline (first rotary encoder) on demand rather than having to wait
# for the seconds on the timer to read "00"
num_rotary_encoders = rotary_encoder_constants["number_of_rotary_encoders"]
seesaw_obj = []

# create seesaw object for each rotary encoder
for i in range(num_rotary_encoders):
   seesaw_obj.append(seesaw.Seesaw(i2c_bus, rotary_encoder_constants["addresses"][i]))
   version = (seesaw_obj[i].get_version() >> 16) & 0xFFFF
   if(version != 4991):
      print(f"Wrong firmware loaded for rotary encoder address 0x{rotary_encoder_constants["addresses"][i]:x}?  Expected 4991")

# set up the rotary encoders a la
# https://github.com/adafruit/Adafruit_CircuitPython_seesaw/blob/main/examples/seesaw_rotary_multiples.py
qt_enc = []
button = []
button_held = []
encoder = []
last_position = []
pixel = []
position = []
for i in range(num_rotary_encoders):
   qt_enc.append(seesaw.Seesaw(i2c_bus, rotary_encoder_constants["addresses"][i]))
   qt_enc[i].pin_mode(24, qt_enc[i].INPUT_PULLUP)   # set up the Adafruit seesaw chip on the rotary encoders
   button.append(digitalio.DigitalIO(qt_enc[i], 24))
   button_held.append(False)
   encoder.append(rotaryio.IncrementalEncoder(qt_enc[i]))
   last_position.append(None)
   pixel.append(neopixel.NeoPixel(qt_enc[i], 6, 1))
   pixel[i].brightness = .01
   pixel[i].fill(0x0000FF)
   position.append(encoder[i].position)
#-------- get list of seconds to report and list of reset times -------
report_times = report_seconds(number_of_samples_per_minute)
reset_report_times = report_resets(report_times)
# -------- initialize PM25_I2C object -------------
pm25 = PM25_I2C(i2c_bus, reset_pin)
print("PM2.5 sensor found")
print_to_display(display, i2c_bus, 9, 3)
# ----------------- server stuff below ------------------
try:   
   response_code, id = check_forwarding_server()
   if(response_code == 200):
      print_to_display(display, i2c_bus, 7, 3, id)
      print(f"🧸 Forwarding server is up with latest id = {id} 🧸")
   else:
      print_to_display(display, i2c_bus, 8, 3)
      print(f"🧸 Forwarding server response_code is {response_code} 🧸")
except Exception as e:
   print(f"💀" * 40)
   print(f"{e} \t Continuing without forwarding...")
   print(f"💀" * 40)
   print_to_display(display, i2c_bus, 8, 3)

degree_symbol = chr(176)
print("+" * 25)
print_toggle = True  # used to control the amount of printing/reporting in the loop
while True:
   time.sleep(0.3)
   try:
      for i in range(num_rotary_encoders):
         position[i] = encoder[i].position %256
         if(position[i] != last_position[i]):
            last_position[i] = position[i]
            pixel[i].fill(colorwheel(position[i]))
         if(not button[i].value and not button_held[i]):
            button_held[i] = True
            pixel[i].brightness = .1
            pixel[i].fill(0xFF00FF)
         # if button pressed, rtc will be synced to ntp time 
         if(i == (num_rotary_encoders-1) and button[i].value and button_held[i]): 
            button_held[i] = False
            pixel[i].brightness = .01
            if set_ntp_time_is_successful(wifi.radio):    # function calls ntp server to set Pico 2 W real time clock
               print_to_display(display, i2c_bus, 4, 5)
               print(f"Set real-time clock to ntp time: {pretty_time(time.localtime())}")
               pixel[i].fill(0x00007F)
               pixel[i].brightness = .05
            else:
               print_to_display(display, i2c_bus, 5, 6)
               pixel[i].fill(0x7F0000)
               pixel[i].brightness = .05
               print(f"Couldn't set real-time clock to ntp time. Continuing anyway with time reading \n{pretty_time(time.localtime())}.")  
      time_string = pretty_time(time.localtime())
      print_time = (time_string.split(":")[2]) in report_times
      if(print_time and print_toggle): # 
         print_toggle = False
         try:
            aqd = pm25.read()
         except RuntimeError:
            print("Unable to read from PM2.5 sensor")
            continue       
         measurements = {
            "pm10s": aqd['pm10 standard'],
            "pm25s": aqd['pm25 standard'],
            "pm100s": aqd['pm100 standard'],
            # "pm10e": aqd['pm10 env'],
            # "pm25e": aqd['pm25 env'],
            # "pm100e": aqd['pm100 env'],
            "pm03um": aqd['particles 03um'],
            # "pm05um": aqd['particles 05um'],
            # "pm1um": aqd['particles 10um'],
            # "pm25um": aqd['particles 25um'],
            # "pm5um": aqd['particles 50um'],
            # "pm10um": aqd['particles 100um']
         }
         report(measurements, display, i2c_bus, time_string)
      reset_print_time = (time_string.split(":")[2])  in reset_report_times
      if(reset_print_time and not print_toggle): # reset print toggle to print again
         print_toggle = True
   except KeyboardInterrupt:
      break    

