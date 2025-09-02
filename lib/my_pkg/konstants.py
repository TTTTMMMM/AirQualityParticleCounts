ntp_constants = {
   "hours_from_GMT": -4,
   "number_of_times_to_try_calling_ntp_server": 6
}
rotary_encoder_constants = {
   "number_of_rotary_encoders": 1,
   "addresses": [0x36]
}
server_constants = {
   "json_get_url_Mac": "http://192.168.1.216:8001/forwarder/metrics/",
   "json_post_url_Mac": "http://192.168.1.216:8001/forwarder/metrics/create/",
   "json_get_particlesizecounts_Mac": "http://192.168.1.170:8001/forwarder/particlesizecounts/",
   "json_post_particlesizecounts_Mac": "http://192.168.1.170:8001/forwarder/particlesizecounts/create/",
   "json_get_url_NAS": "http://192.168.1.232:8001/forwarder/metrics/",
   "json_post_url_NAS": "http://192.168.1.232:8001/forwarder/metrics/create/",
   "json_get_particlesizecounts_NAS": "http://192.168.1.232:8001/forwarder/particlesizecounts/",
   "json_post_particlesizecounts_NAS": "http://192.168.1.232:8001/forwarder/particlesizecounts/create/",
}

number_of_samples_per_minute = 6