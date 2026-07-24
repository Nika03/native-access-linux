# native-access-linux
All things regarding installation of Native Access and plugins from Native Access on Linux

## Foreword
I've spend few past days chatting with Claude, trying to figure stuff out regarding Native Access.

My goal was simple: Get Native Access running on the same Wine Prefix as the installation of FL Studio to get Kontakt 8 Player running.

I have come around certain issues. Native Access doesn't like running under Wine and when it does, Kontakt 8 Player doesn't want to install. 

Getting Native Access is still quite tricky, but thankfully I got it to run somewhat reliably with Lutris and GE-Proton11-1.

Get FL Studio installed with Lutris by adding a Game, searching for FL Studio and installing it with the GUI installer:
<img width="739" height="508" alt="image" src="https://github.com/user-attachments/assets/54d3278e-7a85-4930-b9fd-09bb5fb9c1e4" />

From there, you can run the "Native-Access_2.exe" by running it inside the Wine prefix within Lutris. 

When Native Access demands permissions to install dependencies, you have to install the NTKDaemon located at ``drive_c/Program Files/Native Instruments/Native Access/resources/daemon/win/`` inside the prefix. 

Launching the Native Access app via the installed application located in ``drive_c/Program Files/Native Instruments/Native Access/Native Access.exe`` may not run. 

I am still looking for solutions, but for now, just launch the installer any time you want to start the app. 

## Kontakt 8 Player
Native Access behaves? Good. To install Kontakt 8, you want to do it from the NA interface. 

The Downloads path in NA may not be there, so give it one; can be your user, steamuser or Public but keep it in mind and open that directory in your Linux file explorer or if you're extra nerdy, the terminal.

Start the installation of Kontakt 8 in NA, it will start downloading a zip file to the downloads directory. 

When the download is done, act fast and duplicate that zip file. 

Extract the exe from that zip file. 

The exe is also an archive, so extract it as well with whatever tool you use to open archives. 

I personally use [PeaZip](https://peazip.github.io/) to do that. 

------------------------------------------------------------------------------------------------------------------------------------

Use the Python script to do the actual installation:

``python3 install_kontakt8.py --payload-root "/path/to/extracted/contents/of/executable" --wineprefix "/path/to/wine/prefix"``

The script will move all the data where it's supposed to and make the registry edits so that it can be found by Native Access. 

The installation with the script is hacky, as Native Access does see it but it will not open Kontakt 8. 

FL Studio does see the plugin, it opens and any Kontakt 8 libraries that need Kontakt 8 will be available to it. 

Overall, Kontakt 8 is usable. Kontakt 8 Player versions later than 8.11.1 may not work, as it would require me to re-examine what the installer for the new version is doing.
