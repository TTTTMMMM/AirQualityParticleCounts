from lib.my_pkg.set_ntp_time import set_ntp_time_is_successful, pretty_time
from lib.my_pkg.creds import creds
from lib.my_pkg.konstants import rotary_encoder_constants
from lib.my_pkg.send_to_server import check_forwarding_server
from lib.my_pkg.konstants import number_of_samples_per_minute
from lib.my_pkg.write_to_display import report_seconds, report_resets  
from lib.my_pkg.write_to_display import print_to_display, report    
import board
import time
import wifi
import busio
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel
from rainbowio import colorwheel 
import adafruit_sht4x
import adafruit_sgp30
import adafruit_displayio_ssd1306
from i2cdisplaybus import I2CDisplayBus
import displayio

displayio.release_displays()
i2c_bus = busio.I2C(board.GP5, board.GP4)  # set up an I2C bus using GP5 as clk and GP4 as data 
i2c_bus.unlock()
i2c_bus1 = busio.I2C(board.GP27, board.GP26)  # set up an I2C bus using GP27 as clk and GP26 as data 
i2c_bus1.unlock()
display_bus = I2CDisplayBus(i2c_bus1, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)
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
else:
   print_to_display(display, i2c_bus, 5, 6)
   print(f"Couldn't set real-time clock to ntp time. Continuing anyway with time reading \n{pretty_time(time.localtime())}.")

print_to_display(display, i2c_bus, 6, 5)
# only using rotary encoders to get measurements (last rotary encoder) 
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

# SHT41 is Sensirion Temperature and Humidity sensor
sht = adafruit_sht4x.SHT4x(i2c_bus)          
sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

# SGP30 is Sensirion Air Quality sensor
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c_bus) 
list1 = [hex(i) for i in sgp30.serial]
sgp30.set_iaq_baseline(0x8973, 0x8AAE)
# sgp30.set_iaq_baseline(0x100, 0x100)
temperature, relative_humidity = sht.measurements
# temperature and humidity used for air quality sensor calibration?
sgp30.set_iaq_relative_humidity(celsius=temperature, relative_humidity=relative_humidity)

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
   pixel[i].fill(0x00FF00)
   position.append(encoder[i].position)
#-------- get list of seconds to report and list of reset times -------
report_times = report_seconds(number_of_samples_per_minute)
reset_report_times = report_resets(report_times)
# ----------------- server stuff below ------------------
# response_code = send_to_server({"SGP30 serial #": list1})
connected_to_forwarding_server: bool = False
try:
   response_code, id = check_forwarding_server()
   if(response_code == 200):
      connected_to_forwarding_server = True
      print_to_display(display, i2c_bus, 7, 5, id)
      print(f"🧸 Forwarding server is up with latest id = {id} 🧸")
   else:
      print_to_display(display, i2c_bus, 8, 5)
      print(f"🧸 Forwarding server response_code is {response_code} 🧸")
except Exception as e:
   print(f"💀" * 40)
   print(f"{e} \t Continuing without forwarding...")
   print(f"💀" * 40)
   print_to_display(display, i2c_bus, 8, 5)

degree_symbol = chr(176)
print("+" * 125)
print_toggle = True                        # used to control the amount of printing/reporting in the loop
while True:
   time.sleep(0.4)
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
         if(i == 0 and button[i].value and button_held[i]):  # first rotary encoder will print out the SGP30 baseline
            button_held[i] = False
            pixel[i].brightness = .01
            baseline_eCO2 = sgp30.baseline_eCO2
            baseline_TVOC = sgp30.baseline_TVOC
            time_string = pretty_time(time.localtime())
            measurements = {
                  "baseline_eCO2": f"{baseline_eCO2:X}", 
                  "baseline_TVOC": f"{baseline_TVOC:X}"
                  }
            print(f"{time_string} \t base_eCO2:0x{baseline_eCO2:X} \t base_TVOC:0x{baseline_TVOC:X} \t 🐼")
            print_to_display(display, i2c_bus, 9, 2, measurements=measurements)
         if(i == (num_rotary_encoders-1) and button[i].value and button_held[i]): # last rotary encoder will print all measurements
            button_held[i] = False
            pixel[i].brightness = .01
            time_string = pretty_time(time.localtime())
            temperature, relative_humidity = sht.measurements
            temperature = temperature * (9/5) + 32.0
            eCO2 = sgp30.eCO2
            tVOC = sgp30.TVOC
            pixel[i].fill(0x00FFFF)  
            measurements = {
               "temperature": f"{temperature:3.1f}", 
               "humidity": f"{relative_humidity:3.1f}", 
               "eCO2": f"{eCO2:d}", 
               "TVOC": f"{tVOC:d}"
                }
            report(measurements, display, i2c_bus, time_string)    
      time_string = pretty_time(time.localtime())
      print_time = (time_string.split(":")[2]) in report_times
      if(print_time and print_toggle): # 
         print_toggle = False
         temperature, relative_humidity = sht.measurements
         temperature = temperature * (9/5) + 32.0
         eCO2 = sgp30.eCO2
         tVOC = sgp30.TVOC 
         measurements = {
               "temperature": f"{temperature:3.1f}", 
               "humidity": f"{relative_humidity:3.1f}", 
               "eCO2": f"{eCO2:d}", 
               "TVOC": f"{tVOC:d}"
                }
         report(measurements, display, i2c_bus, time_string) 
      reset_print_time = (time_string.split(":")[2])  in reset_report_times
      if(reset_print_time and not print_toggle): # reset print toggle to print again
         print_toggle = True
   except KeyboardInterrupt:
      break    