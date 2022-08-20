Base level documentation below:

This project is structured as a django website. Below is an explanation of what each directory means.

### main

This is where all the core logic is for the project. This is a django 'app'.

migrations, __ init__.py, admin.py, apps.py, models.py, tests.py: *Unmodified Django template files*

templatetags: *Used for python logic when templating (passing custom data that determines the content of a webpage)*

config.py: *Handles the website config, which determines what devices to display information for*

information_provider.py: *API for devices to tell the website how to read information about their current state from
them*

state.py: *Basic information about the state of the site, like device information and whether logging is enabled*

urls.py: *Tells django what code to run when a url is opened*

views.py: *The actual custom code that's being run, tells django how to open webpages that are populated with that*

### SkillbossDebugWebsite

__ init__.py, asgi.py, wsgi.py: *Unmodified Django template files*

urls.py: *tells django to treat the app's urls as its own*

settings.py: *important file that handles the django configuration. Environment variables are set here!*

### static

Resources like css, js, and assets are stored here.

### templates

Django templates are stored here.

### config.json

The config file for the website. Please see config.py for documentation.

### manage.py

Used to perform tasks like starting and stopping the website.

To start the website:

1. navigate to the directory of manage .py
2. python manage.py runserver 0.0.0.0:8000

### Debugging Options

1. in state.py you can set simulated to True to use simulated devices instead of config devices
2. check console for known exceptions. For example, a quanser device may accept a connection but not broadcast data to
   it and may consequently be disconnected.
3. realize that some devices may only accept 1 connection at once and if another device is connected the connection may
   be refused.
4. try connecting to a device using sockets outside of this program to see if you can connect there.
   ```python
   import socket
   import struct
   
   client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   client.connect(('192.168.2.64', 18001))
   active_connection = True
   data = client.recv(400)
   
   print("Data length: " + str(len(data)))
   
   for i in range(0, int(len(data) / 8)):
       print(struct.unpack_from('d', data, i * 8)[0])

   ```
5. Check the control panel to see if data logging is disabled or enabled.
6. Try rebooting the raspberry PI server or checking its log if errors relate to the PLC in any way
7. If a device wasn't connected when the website was started but now is, hit the connection button in the control panel
   to refresh connections.