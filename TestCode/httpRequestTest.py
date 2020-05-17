import requests
import argparse

url = "http://10.0.0.19:3000/log"
log = { "name": "RemotePiTest", "state": True }
x = requests.post(url, data = log)
print(x.status_code)