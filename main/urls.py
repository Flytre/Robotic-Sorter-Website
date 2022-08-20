from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('devices/<device_id>', views.device_data_display, name='device-data-display'),
    path('tables/<device_id>', views.table, name='table'),
    path('raw/<device_id>',views.raw,name='raw'),
    path('control_panel', views.control_panel, name='control-panel'),
    path('set_logging', csrf_exempt(views.set_logging), name='set-logging'),
    path('reconnect-devices', csrf_exempt(views.reconnect_devices), name='reconnect-devices')

]
