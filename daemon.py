import time
import subprocess
import json
import uuid
from datetime import datetime

import RPi.GPIO as gpio
from hx711 import HX711

import config

def take_photo():
    filename = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + daemon_id + ".jpg"
    args = [
        "/usr/bin/v4l2-ctl",
        "-d", config.camera_device,
        "--set-fmt-video", config.photo_format + ",pixelformat=MJPG",
        "--stream-mmap",
        "--stream-count", "1",
        "--stream-to", config.tmpdir + "/" + filename,
    ]
    result = subprocess.run(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("failed to take photo: {}".format(result.returncode), result.stdout.decode('utf-8'))
    return filename

def build_json(pictures):
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    raw = {"daemon_id": daemon_id,
     "serial": daemon_serial,
     "year": year,
     "month": month,
     "day": day,
     "pictures": pictures,
    }
    return json.dumps(raw)

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(config.hx711_reference_unit)
hx.reset()
hx.tare()

daemon_id = str(uuid.uuid4())
daemon_serial = 1

if config.debug:
    print("init done", daemon_id)

signal_sent_at = None

try:
    while True:
        val = hx.get_weight(1)
        hx.power_down()
        hx.power_up()

        if config.debug:
            print(val)
        detected = val >= config.load_threshold
        if detected:
            if signal_sent_at == None:
                if config.debug:
                    print("cat detected")
                pictures = []
                for i in range(0, config.photo_count):
                    picture = take_photo()
                    pictures.append(picture)
                    time.sleep(1)
                payload = build_json(pictures)
                daemon_serial += 1
                if config.debug:
                    print(payload)
                # send_json(json)
            signal_sent_at = time.time()
        elif signal_sent_at != None:
            now = time.time()
            if now - signal_sent_at > config.reset_timeout:
                signal_sent_at = None
                if config.debug:
                    print("sensor reset")

        time.sleep(config.loop_interval)
except (KeyboardInterrupt, SystemExit):
    print("bye!")
    gpio.cleanup()

