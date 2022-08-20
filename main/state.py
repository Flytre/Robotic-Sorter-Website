from typing import List

from . import config
from . import information_provider
import threading

cfg = config.load_config('config.json')
simulated = True
devices: List[information_provider.InformationProvider] = information_provider.load_information_providers(cfg,
                                                                                                          simulated)
logging = False


# Pseudo-Recursive: update is called in initialization and will call itself every quarter second forever
def update():
    for device in devices:
        device.periodic_update()  # this refreshes the data each device receives
    threading.Timer(0.15, update).start()


# Control Panel : Reconnect
def connect_devices():
    for device in devices:
        thread = threading.Thread(target=device.full_initialize)
        thread.start()


# Control Panel: Enable Logging
def enable_logging():
    global logging
    logging = True
    for device in devices:
        device.enable_logging()


# Control Panel: Disable Logging
def disable_logging():
    global logging
    logging = False
    for device in devices:
        device.disable_logging()


# Initialization Code
connect_devices()
threading.Timer(0.25, update).start()
