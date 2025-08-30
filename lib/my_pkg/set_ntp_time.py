import adafruit_ntp
import rtc
import adafruit_ntp
import socketpool
from time import sleep
from .konstants import ntp_constants

list_of_months = [
   'Jan', 
   'Feb', 
   'Mar', 
   'Apr', 
   'May', 
   'Jun', 
   'Jul', 
   'Aug', 
   'Sep', 
   'Oct', 
   'Nov', 
   'Dec'
   ]

def set_ntp_time_is_successful(radio) -> bool:
    number_calls_to_ntp_server = ntp_constants["number_of_times_to_try_calling_ntp_server"]
    success:bool = False
    pool = socketpool.SocketPool(radio)
    rtc_obj = rtc.RTC()
    hours_from_GMT = ntp_constants["hours_from_GMT"]
    times_called = 1
    while times_called < number_calls_to_ntp_server:
        try:
            ntp = adafruit_ntp.NTP(pool, tz_offset = hours_from_GMT)
            rtc_obj.datetime = ntp.datetime
            success = True
            # print(f"Number of calls to ntp server: {times_called}")
            times_called = number_calls_to_ntp_server + 1
        except:
            times_called += 1
            sleep(1)
    return success

def fix_hour(pretty_hour:int) -> int:
   if(pretty_hour < 0):
      return(24 + pretty_hour)
   else:
      return pretty_hour
    
def pretty_time(curr_time:tuple) -> str:
    month = list_of_months[curr_time[1]-1]
    pretty_hour = fix_hour(curr_time[3])
    time_string = f"{curr_time[0]}-{month}-{curr_time[2]:02d} {(pretty_hour):02d}:{(curr_time[4]):02d}:{(curr_time[5]):02d}"
    return time_string
