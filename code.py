from lib.my_pkg.set_ntp_time import set_ntp_time_is_successful, pretty_time
from lib.my_pkg.creds import creds
from lib.my_pkg.konstants import rotary_encoder_constants
from lib.my_pkg.send_to_server import check_forwarding_server, post_to_server
from lib.my_pkg.write_to_display import print_to_display, report
import board
import time
import wifi
import busio
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel
from rainbowio import colorwheel
from i2cdisplaybus import I2CDisplayBus
import displayio
import terminalio 
from adafruit_display_text import label
from i2cdisplaybus import I2CDisplayBus
from adafruit_displayio_sh1107 import SH1107, DISPLAY_OFFSET_ADAFRUIT_128x128_OLED_5297

displayio.release_displays()
i2c_bus = busio.I2C(board.GP5, board.GP4)  # set up an I2C bus using GP5 as clk and GP4 as data 
i2c_bus.unlock()
display_bus = I2CDisplayBus(i2c_bus, device_address=0x3D)
display = SH1107(
    display_bus,
    width=128,
    height=128,
    display_offset=DISPLAY_OFFSET_ADAFRUIT_128x128_OLED_5297,
    rotation=270,
)
# ----------------
# Make the display context
WIDTH = 128
HEIGHT = 128
BORDER = 2
splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle in black
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
splash.append(inner_sprite)

# Draw some label text
name_text = "Monochrome 1.12in"
name_text_area = label.Label(terminalio.FONT, text=name_text, x=8, y=8)
splash.append(name_text_area)
size_text = "128x128"
size_text_area = label.Label(terminalio.FONT, text=size_text, scale=2, x=8, y=25)
splash.append(size_text_area)
oled_text = "OLED"
oled_text_area = label.Label(terminalio.FONT, text=oled_text, scale=3, x=9, y=54)
splash.append(oled_text_area)

while True:
    pass
# -----------------
print_to_display(display, i2c_bus, 1, 1)

try:
   wifi.radio.connect(creds['ssid'], creds['password'])   # connect to wifi
   # print_to_display(display, i2c_bus, 2, 5)
except Exception as e:
   # print_to_display(display, i2c_bus, 3, 5)
   print(f"Errored out trying to establish wifi:\n{e}\nWill not proceed further with script...")
   while True:   # do nothing forever
      pass           
    
if set_ntp_time_is_successful(wifi.radio):    # function calls ntp server to set Pico 2 W real time clock
   # print_to_display(display, i2c_bus, 4, 5)
   print(f"Set real-time clock to ntp time: {pretty_time(time.localtime())}")
else:
   # print_to_display(display, i2c_bus, 5, 6)
   print(f"Couldn't set real-time clock to ntp time. Continuing anyway with time reading \n{pretty_time(time.localtime())}.")

# print_to_display(display, i2c_bus, 6, 5)
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
      print_time = (time_string.split(":")[2]) == "00" or (time_string.split(":")[2]) == "01"
      if(print_time and print_toggle): # all measurements will be printed at the top of the minute
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
      reset_print_time = (time_string.split(":")[2]) == "02" or (time_string.split(":")[2]) == "03"
      if(reset_print_time and not print_toggle): # reset print toggle to print again
         print_toggle = True
   except KeyboardInterrupt:
      break    

