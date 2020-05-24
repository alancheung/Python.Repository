from __future__ import print_function
from datetime import datetime, time, timedelta
from time import sleep
import json
import requests

import sys
import argparse

x = {
	"Lights": ["Office One", "Office Two", "Office Three"],
	"TurnOff": "true",
	"Duration": 10000,
	"Hue": 0.88,
	"Saturation": 0.0,
	"Brightness": 1.0,
	"Kelvin": 2500
}

req = requests.post('http://localhost:3000/api/lifx', data = x, timeout=30)
print(req.status_code)