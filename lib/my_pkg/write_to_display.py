import displayio
from adafruit_display_text import label
import terminalio
import time 
import wifi
from lib.my_pkg.set_ntp_time import pretty_time 
from lib.my_pkg.send_to_server import post_to_server

def print_to_display(display, 
                     i2c_bus, 
                     block_number: int, 
                     delay_in_secs: int, 
                     id: str="-",
                     fb_id: str='',
                     measurements: dict={}) -> None:
   display_lines = []
   if(block_number==1):
      display_lines.append(f"Connecting to Wifi")
      display_lines.append(f"-")
      display_lines.append("-")
      display_lines.append("-")
      display_lines.append("-")
      write_to_display(display, display_lines)
   elif(block_number==2):
      display_lines.append(f"Connected to Wifi")
      display_lines.append(f"IP: {wifi.radio.ipv4_address}")
      display_lines.append("Setting RTC clock")
      display_lines.append("-")
      display_lines.append("-")
      write_to_display(display, display_lines)
   elif(block_number==3):
      display_lines.append(f"Could not ")
      display_lines.append(f"connect to")
      display_lines.append("wifi")
      display_lines.append("STOPPING...")
      display_lines.append("-")
      write_to_display(display, display_lines)
   elif(block_number==4):
      time_string = pretty_time(time.localtime())
      display_lines.append(f"Connected to Wifi")
      display_lines.append("Set RTC clock to")
      display_lines.append(f"{time_string[:-3]}")
      display_lines.append(f"-")
      display_lines.append("-")
      write_to_display(display, display_lines)
   elif(block_number==5):
      time_string = pretty_time(time.localtime())
      display_lines.append(f"{time_string[:-3]}")
      display_lines.append(f"Could not")
      display_lines.append(f"set real-time")
      display_lines.append("clock")
      display_lines.append("-")
      write_to_display(display, display_lines)
   elif(block_number==6):
      time_string = pretty_time(time.localtime())
      display_lines.append(f"{time_string[:-3]}")
      display_lines.append(f"IP: {wifi.radio.ipv4_address}")
      display_lines.append("-")
      display_lines.append("-")
      display_lines.append("-")
      write_to_display(display, display_lines)
   elif(block_number==7):
      time_string = pretty_time(time.localtime())
      display_lines.append(f"{time_string[:-3]}")
      display_lines.append("Connected to")
      display_lines.append("forwarding server!")
      display_lines.append("Awaiting measurement")
      display_lines.append(f"Last id: {id}")
      write_to_display(display, display_lines)
   elif(block_number==8):
      time_string = pretty_time(time.localtime())
      display_lines.append(f"{time_string[:-3]}")
      display_lines.append("Forwarding")
      display_lines.append("server appears")
      display_lines.append("to be down")
      display_lines.append("-")
      write_to_display(display, display_lines)
   elif(block_number==9):
      time_string = pretty_time(time.localtime())
      display_lines.append(f"{time_string}")
      display_lines.append(f"PM2.5 sensor found")
      display_lines.append(f"-")
      display_lines.append(f"-")
      display_lines.append("-")
      write_to_display(display, display_lines)
   elif(block_number==10):
      time_string = pretty_time(time.localtime())
      temperature = measurements["temperature"]
      relative_humidity = measurements["humidity"]
      eCO2 = measurements["eCO2"]
      TVOC = measurements["TVOC"]
      short_fb_id = fb_id[:8]
      display_lines.append(f"{time_string}")
      display_lines.append(f"{temperature} F \t{relative_humidity}%")
      display_lines.append(f"eCO2: \t{eCO2} ppm")
      display_lines.append(f"TVOC: \t{TVOC} ppb")
      display_lines.append(f"id:{id}\t{short_fb_id}")
      write_to_display(display, display_lines)
   else:
      time_string = pretty_time(time.localtime())
      display_lines.append(f"{time_string}")
      display_lines.append(f"Wrong block")
      display_lines.append(f"number param")
      display_lines.append(f"in print")
      display_lines.append("-")
      write_to_display(display, display_lines)
   time.sleep(delay_in_secs)
   return None

def write_to_display(display, text_list: list) -> None:
   # Make the display context
   BORDER = 2
   splash = displayio.Group()
   display.root_group = splash

   color_bitmap = displayio.Bitmap(128, 128, 1)
   color_palette = displayio.Palette(1)
   color_palette[0] = 0xFFFFFF  # White
   bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
   splash.append(bg_sprite)

   # Draw a smaller inner rectangle in black
   inner_bitmap = displayio.Bitmap(128 - BORDER * 2, 128 - BORDER * 2, 1)
   inner_palette = displayio.Palette(1)
   inner_palette[0] = 0x000000  # Black
   inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
   splash.append(inner_sprite)

   text_area = label.Label(terminalio.FONT, text=text_list[0], x=3 + BORDER, y=6 + BORDER)
   splash.append(text_area)
   text_area = label.Label(terminalio.FONT, text=text_list[1], x=9 + BORDER, y=18 + BORDER)
   splash.append(text_area)
   text_area = label.Label(terminalio.FONT, text=text_list[2], x=9 + BORDER, y=31 + BORDER)
   splash.append(text_area)
   text_area = label.Label(terminalio.FONT, text=text_list[3], x=9 + BORDER, y=45 + BORDER)
   splash.append(text_area)   
   text_area = label.Label(terminalio.FONT, text=text_list[4], x=3 + BORDER, y=58 + BORDER)
   splash.append(text_area)   

   return None

def report(measurements: dict={}, display: any= {}, i2c_bus: any= {}, time_string: str="No time")-> None:
   id = -1
   firebase_id = -1
   forwarder = "down"
   try:
      temperature = measurements['temperature']
      relative_humidity = measurements['humidity']
      eCO2 = measurements['eCO2']
      tVOC = measurements['TVOC']
      response_code, id, firebase_id, forwarder = post_to_server(measurements)
      if(response_code == 201):
         # print(f"🤖 {id} 🤖")
         print_to_display(display, i2c_bus, 10, 1, id, firebase_id, measurements)   
      else:
         print(f"🧸 Error from Forwarding server: {response_code} 🧸")
   except Exception as e:
      print(f"💀 {e} 💀")     
   print(f"{time_string} \t {temperature}℉ \t {relative_humidity:}% \t eCO2:{eCO2}ppm \t TVOC:{tVOC}ppb \t {id} \t {firebase_id} \t {forwarder} 🐳")

   return None   

def report_seconds(n:int=1) -> list:
    if ((n <= 0) or (n == 1) or (n > 15)) :
        return ["00"]
    numbers = []
    step =60/n
    for i in range(n):
        num = round(i * step)          # Calculate the number and round it to the nearest integer
        num = max(0, min(60, num))     # Ensure the number stays within the 0-60 range
        numbers.append(f"{num:02d}")   # Format the number as a 2-digit string with leading zeros
    
    return numbers

def report_resets(report_times:list) -> list:
   int_list = int_list = [int(s) for s in report_times]
   reset_ints = [x + 2 for x in int_list]           # 2 seconds after reporting, print toggle is eligible to reset
   reset_strings = [f"{num:02d}" for num in reset_ints]
   return reset_strings