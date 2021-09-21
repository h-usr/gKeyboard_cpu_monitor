# gKeyboard cpu monitor
Python script to manage G series keyboard on linux.<br/>
LED color changes based on CPU load (0% green - 100% red).<br/>
Keyboard blinks when receiving desktop notifications specified in XML file; blink color and duration can be specified.<br/>
Developed and tested on Linux Mint 20.1 (Cinnamon) with a G213 keyboard.<br/>
NOTE: installing https://github.com/MatMoul/g810-led is required.<br/>

# Usage
The script is intended to be automatically executed at startup and run in background.

```
python3 gkb_cpu_monitor.py [-notify] [-persistent] [-verbose] 
```
 - [-notify] Enables notification blinking feature; you need to have a 'notifications.xml' in the same folder (more on that later)<br/>
 - [-persistent] Will not stop the script if the keyboard is disconnected or the communication fails<br/>
 - [-verbose] Will print RGB values and active notifications; intended only for debug purposes<br/>

# notifications.xml format
To set LED color and blinking specifics for each notification, the file should look something like this:
```
<?xml version="1.0" encoding="UTF-8"?>
<notifications>
  <notification>
    <name>Telegram Desktop</name>
    <color>0,190,255</color>
    <count>2</count>
    <interval>0.3</interval>
  </notification>
  <notification>
    <name>Spotify</name>
    <color>255,255,255</color>
    <count>1</count>
    <interval>0.2</interval>
  </notification>
</notifications>
```
Color is in RGB format and duration of blinks is expressed in seconds.

__Hope you like it! Please leave feedback!__
