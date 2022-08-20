from typing import Optional

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from . import state

# Create your views here.
from .information_provider import InformationProvider


def index(request):
    return render(request, "main/home.html", {
        "devices": [device.to_attr_dict() for device in state.devices]
    })


def get_device_with_id(device_id: str) -> Optional[InformationProvider]:
    device: Optional[InformationProvider] = None
    for d in state.devices:
        if d.id == device_id:
            device = d
            break
    return device


def device_data_display(request, device_id):
    device: Optional[InformationProvider] = get_device_with_id(device_id)

    if device is None:
        return render(request, "main/error.html", {
            "error": "Device not found"
        })

    if not device.active_connection:
        return render(request, "main/error.html", {
            "error": "Device not connected"
        })

    return render(request, "main/device-data-display.html", {
        "device": device.to_attr_dict(),
        "headers": device.get_data_value_headings(),
        "data": device.data
    })


def table(request, device_id):
    device: Optional[InformationProvider] = get_device_with_id(device_id)
    if device is None:
        return HttpResponse("Error: device " + device_id + " not found.")

    return render(request, "main/table.html", {
        "headers": device.get_data_value_headings(),
        "data": device.data
    })


def control_panel(request):
    return render(request, "main/control_panel.html", {
        "logging": state.logging
    })


def set_logging(request):
    if request.method != 'POST':
        return

    if 'logging' in request.POST.keys():
        logging = False if request.POST['logging'] == 'false' else True
        if logging:
            state.enable_logging()
        else:
            state.disable_logging()
        return JsonResponse({
            "logging": state.logging
        })
    return JsonResponse({
        "logging": "error in request"
    })


def reconnect_devices(request):
    if request.method != 'POST':
        return
    state.connect_devices()
    return HttpResponse("success")


def raw(request, device_id):
    device: Optional[InformationProvider] = get_device_with_id(device_id)
    if device is None:
        return HttpResponse("Error: device " + device_id + " not found.")
    return JsonResponse({
        "val": list([device.data[key]['value'] for key in device.data.keys()])
    })
