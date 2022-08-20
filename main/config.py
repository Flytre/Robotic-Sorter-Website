from typing import List
from typing import Any
from dataclasses import dataclass
import json


# config.py
# Author: Aaron Rahman <cyber@umich.edu>
# Date of documentation: 8/15/2022

# The purpose of this file is to standardize the format of the configuration file for this program and
# make runtime problems compile time problems by using objects instead of dictionaries

# To read a config, read in a .json file as a dictionary and then call from_dict in the class Config. Writing configs
# is not supported.

# Format:
# root
#   entries: list of objects
#       an entry (object):
#           name: The display name of a device
#           id:   The internal id the device should have. Use [a-zA-Z0-9\-]+
#           type  The type of the device. Can be 'skill-boss-logistics', 'qarm', 'rotatory', 'qbot', or 'pi-plc-server'.
#           ip:   The ip address of the device.
#           port: The port of the device. This field is not guaranteed to be respected.
#   datapoints: object. Stores the datapoints that a quanser device is transmitting.
#           At the time of this writing, these devices broadcast information as a stream of 8-byte doubles.
#           The config options below name each double received so they are human readable.
#           For example, ['x','y','z','current']
#       qarm: list of datapoints for the qarm.
#       qbot: list of datapoints for the qbot.
#       rotatory: list of datapoints for the rotatory
@dataclass
class ConfigEntry:
    name: str
    id: str
    type: str
    ip: str
    port: str

    @staticmethod
    def from_dict(obj: Any) -> 'ConfigEntry':
        _name = str(obj.get("name"))
        _id = str(obj.get("id"))
        _type = str(obj.get("type"))
        _ip = str(obj.get("ip"))
        _port = str(obj.get("port"))
        return ConfigEntry(_name, _id, _type, _ip, _port)


@dataclass
class DatapointConfig:
    qarm: List[str]
    qbot: List[str]
    rotatory: List[str]

    @staticmethod
    def from_dict(obj: Any) -> 'DatapointConfig':
        _qarm = [y for y in obj.get("qarm")]
        _qbot = [y for y in obj.get("qbot")]
        _rotatory = [y for y in obj.get("rotatory")]
        return DatapointConfig(_qarm, _qbot, _rotatory)


@dataclass
class Config:
    entries: List[ConfigEntry]
    datapoints: DatapointConfig

    @staticmethod
    def from_dict(obj: Any) -> 'Config':
        _entries = [ConfigEntry.from_dict(y) for y in obj.get("entries")]
        _config = DatapointConfig.from_dict(obj.get("datapoints"))
        return Config(_entries, _config)


# Loads the config file at the given location.
# Does not check if the file exists or is valid json.
def load_config(path: str):
    return Config.from_dict(json.load(open(path)))
