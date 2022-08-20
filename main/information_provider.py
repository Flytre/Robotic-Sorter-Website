import csv
import json
import os
import random
import socket
import struct
from abc import abstractmethod
from datetime import datetime
from typing import List

from pycomm3 import LogixDriver, CommError, Tag

from . import config


# Explains how to connect, retrieve, and process information for a custom device
class InformationProvider:
    data: dict  # stores the most recent data for a device. keys should be datapoint names, and the value should be a
    # dictionary representing different properties of the value. the 'value' property is mandatory for this and
    # should contain the raw value. Examples of supplemental properties would be data-type and dimensionality.

    # sample data dictionary:
    # {
    #   "length" : {"value" : 3, "type" : "INT" },
    #   "color" : {"value" : "#FF0000", "type" : "COLOR"}
    # }

    name: str
    id: str
    ip: str
    port: int
    active_connection: bool
    cfg: config.Config
    log: bool
    init: bool

    def __init__(self, name: str, id: str, ip: str, port: int, cfg: config.Config):
        self.name = name
        self.id = id
        self.ip = ip
        self.port = port
        self.cfg = cfg
        self.data = dict()
        self.active_connection = False
        self.log = False
        self.init = False

    # functionality that should be run before getting data from a target device for the first time. example: figuring
    # out what data needs to be gotten in the first place. After this method, 'data' should contain real or dummy data.
    @abstractmethod
    def initialize_data(self):
        pass

    # refreshes the data with up-to-date information from the device.
    @abstractmethod
    def update_data(self):
        pass

    # connect to the target device when this method is called.
    @abstractmethod
    def connect(self):
        pass

    # logs a header row to the CSV file storing the data for this device over time
    def log_header(self):
        writer = csv.writer(open(os.path.join("csv", self.name + ".csv"), 'a', newline=''))
        if not self.active_connection:
            writer.writerow(["Err no connection"])
            return
        row = ['Date']
        for datapoint_key in self.data:
            row.append(datapoint_key)
        writer.writerow(row)

    # logs a data row to the CSV file storing the data for this device over time
    def log_row(self):
        if not self.active_connection:
            return
        now = datetime.now().strftime("%H:%M:%S %f")
        row = [now]
        for datapoint_key in self.data:
            row.append(self.data[datapoint_key]['value'])
        writer = csv.writer(open(os.path.join("csv", self.name + ".csv"), 'a', newline=''))
        writer.writerow(row)

    # used for templating to convert a device into json
    def to_attr_dict(self):
        return {
            "name": self.name,
            "id": self.id,
            "ip": self.ip,
            "port": self.port,
            "connected": self.active_connection
        }

    # returns the format of datapoint values as a dictionary where keys are datapoint value keys and values are their
    # display names. each key represents a datapoint, but how the information stored in the value dictionary is
    # represented here. for example, if a sample datapoint is "client_name" : {"value: "tim", "type" : "STRING",
    # "dimension": (1,3)}, this method should return {"value" : "Value", "type" : "Type", "dimension" :
    # "Dimensionality"}
    @abstractmethod
    def get_data_value_headings(self) -> dict:
        pass

    # enables logging for this device
    def enable_logging(self):
        self.log = True
        self.log_header()

    # disables logging for this device
    def disable_logging(self):
        self.log = False

    # connects to device and initializes data
    def full_initialize(self):
        self.connect()
        self.initialize_data()
        self.init = True

    # refreshes data and logs if applicable
    def periodic_update(self):
        if not self.init:
            return

        if self.active_connection:
            self.update_data()
        if self.active_connection and self.log:
            self.log_row()


# Implementation class for interfacing with Quanser Devices
class QuanserInformationProvider(InformationProvider):
    client: socket
    DOUBLE_BYTES = 8

    @abstractmethod
    def get_datapoints(self) -> List[str]:
        pass

    def connect(self):
        if self.active_connection:
            return

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)

        try:
            client.connect((self.ip, int(self.port)))
            self.active_connection = True
        except:
            self.active_connection = False

        self.client = client

    def initialize_data(self):
        datapoints = self.get_datapoints()
        bytestream: bytes = self.get_data()

        if not self.active_connection:
            return

        for i in range(0, len(datapoints)):
            self.data[datapoints[i]] = {
                "type": "DOUBLE",
                "value": struct.unpack_from('d', bytestream, i * 8)[0]
            }

    def get_data(self):

        if not self.active_connection:
            return b''

        datapoints = self.get_datapoints()
        self.client.settimeout(1)

        try:
            bytestream = self.client.recv(len(datapoints) * QuanserInformationProvider.DOUBLE_BYTES)
            return bytestream
        except:
            print("Quanser device \"" + self.name + "\" is not supplying data.")
            self.active_connection = False
            return b''

    def update_data(self):
        self.initialize_data()

    def get_data_value_headings(self):
        return {
            "type": "Type",
            "value": "Value"
        }


class QArmInformationProvider(QuanserInformationProvider):

    def get_datapoints(self) -> List[str]:
        return self.cfg.datapoints.qarm


class QBotInformationProvider(QuanserInformationProvider):

    def get_datapoints(self) -> List[str]:
        return self.cfg.datapoints.qbot


class RotatoryInformationProvider(QuanserInformationProvider):

    def get_datapoints(self) -> List[str]:
        return self.cfg.datapoints.rotatory


# Implementation class for interfacing with Allen Bradley PLCs directly (not via raspberry pi relay)
class AllenBradleyInformationProvider(InformationProvider):
    plc: LogixDriver

    def connect(self):
        if self.active_connection:
            return

        plc = LogixDriver(self.ip)
        try:
            plc.open()
            self.active_connection = True
        except CommError:
            self.active_connection = False
        self.plc = plc

    def initialize_data(self):
        if not self.active_connection:
            return
        raw_data: List[dict]

        try:
            raw_data = self.plc.get_tag_list()
        except CommError:
            self.active_connection = False
            return

        for tag in raw_data:
            if 'external_access' not in tag:
                continue
            external_access = str(tag['external_access'])
            if 'read' not in external_access.lower():
                continue
            self.data[tag['tag_name']] = {
                "type": tag['data_type_name'],
                "dimension": tag['dim'],
                "access": tag['external_access'],
                "value": "unknown"
            }

    def update_data(self):
        values: List[Tag]

        if len(self.data.keys()) == 0:
            return

        try:
            values = self.plc.read(*self.data.keys())
        except CommError:
            self.active_connection = False
            return

        for val in values:
            if val.error is not None:
                self.data[val.tag]['value'] = None
            else:
                self.data[val.tag]['value'] = str(val.value)

    def get_data_value_headings(self) -> dict:
        return {
            "type": "Type",
            "dimension": "Dimension",
            "access": "Access",
            "value": "Value"
        }


# Implementation class for interfacing with a raspberry PI server that communicates with PLCs
class RaspberryPiRelayInformationProvider(InformationProvider):
    client: socket

    def connect(self):
        if self.active_connection:
            return

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)

        try:
            client.connect((self.ip, int(self.port)))
            self.active_connection = True
        except:
            self.active_connection = False

        self.client = client

    def get_json_with_termination_data(self, command: str):
        if not self.active_connection:
            return False

        self.client.send(str.encode(command))

        response: bytes = bytes()
        while True:
            chunk = self.client.recv(4096000)
            response += chunk
            val = int.from_bytes(chunk[-1:], "big")
            if val == 191:
                break
        return json.loads((response[0:len(response) - 1]))

    def initialize_data(self):
        info: dict = self.get_json_with_termination_data("tag all")
        for tag in info.keys():
            info[tag]['value'] = "Unknown"
        self.data = info

    def update_data(self):
        values = self.get_json_with_termination_data("tag read-all")

        for tag in values.keys():
            if tag in self.data:
                self.data[tag]['value'] = str(values[tag])

    def get_data_value_headings(self) -> dict:
        return {
            "type": "Type",
            "dim": "Dimension",
            "access": "Access",
            "value": "Value"
        }


# debug information provider for simulating hardware
class SimulatedInformationProvider(InformationProvider):

    def __init__(self, name: str, id: str, cfg: config.Config):
        super().__init__(name, id, socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff))),
                         random.randint(0, 256), cfg)

    def connect(self):
        if random.random() > 0.5:
            self.active_connection = True

    def initialize_data(self):

        if not self.active_connection:
            return
        self.data['date'] = {
            "type": "DATE",
            "value": datetime.now().strftime("%H:%M:%S")
        }
        self.data['rng'] = {
            "type": "DOUBLE",
            "value": format(random.random(), ".2f")
        }

    def update_data(self):
        self.initialize_data()

    def get_data_value_headings(self):
        return {
            "type": "Type",
            "value": "Value"
        }


def create_device(device_type: str, *params) -> InformationProvider:
    if device_type == 'skill-boss-logistics':
        return AllenBradleyInformationProvider(*params)
    if device_type == 'qarm':
        return QArmInformationProvider(*params)
    if device_type == 'qbot':
        return QBotInformationProvider(*params)
    if device_type == 'rotatory':
        return RotatoryInformationProvider(*params)
    if device_type == 'pi-plc-server':
        return RaspberryPiRelayInformationProvider(*params)

    assert "Invalid device type " + device_type + "in config"


# loads all information providers from a config file
def load_information_providers(cfg: config.Config, simulated=False) -> List[InformationProvider]:
    if simulated:
        return [SimulatedInformationProvider("Simulated #" + str(i), "simulated-" + str(i), cfg) for i in range(0, 10)]
    else:
        return [create_device(entry.type, entry.name, entry.id, entry.ip, entry.port, cfg) for entry in cfg.entries]
