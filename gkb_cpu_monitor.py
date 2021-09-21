#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import time
import os
import threading
import argparse
import psutil
import xml.etree.ElementTree as xml_parser
from dbus import SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository.GLib import MainLoop

"""
This script changes the G series keyboard led color based on the CPU load
You can define an XML file to make the keyboard blink with freedesktop notifications 
NOTE: https://github.com/MatMoul/g810-led is required
"""

#Global variables

NOTIFY = "" #Stores last dbus notification name
SAMPLING = 0.2 #CPU load calculation interval
SAMPLES = 25 #CPU load cache
NOTIFICATION_SETTINGS_FILE = "notifications.xml" #Notification settings file path
NOTIFICATION_SETTINGS_MANDATORY_ATTRIBUTES = ("name", "color", "count", "interval") #Mandatory attributes of each notification setting, to be read from XML file

#General purpose functions

def limit(min_thr, max_thr, number):
    return max(min(number, max_thr), min_thr)

def int_to_hexstring(dec):
    """
    Returns a string containing the hexadecimal value of the passed integer
    """
    out = str(hex(dec))[2:] #'\xff' to 'ff'
    if ((len(out) % 2) != 0): #Adds '0' if number of characters is odd
        out = "0" + out
    return out.upper()

#Keyboard color change functions

def get_load_color(percentage):
    """
    Returns an RGB value array (0-255) based on green-red scale
    0% load = 100% green, 0% red
    50% load = 50% green, 50% red
    100% load = 0% green 100% red
    """
    percentage = percentage / 100
    rgb = [2 * percentage, 2 * (1 - percentage), 0] #RGB values between 0 and 2 by direct and reverse percentage scale
    for i in range(3):
        rgb[i] = int(limit(0, 1, rgb[i]) * 255 ) #Transforms 0-1 value in 0-255 values
    return rgb

def set_keyboard_color(rgb, ignore_errors=0):
    """
    Calls g810-led with rgb values as argument
    If an error occurs, gives warning and stops script
    """
    color_string="" #String used by g810-led to set color
    for color in rgb:
        color_string+=int_to_hexstring(limit(0, 255, color))
    try:
        subprocess.check_output(["g810-led", "-a", color_string])
    except FileNotFoundError:
        print("Program g810-led not found; install it from https://github.com/MatMoul/g810-led")
        exit()
    except:
        if not ignore_errors:
            print("Program g810-led failed; check keyboard connection")
            exit()

def notification_blink(color1, color2=[0,0,0], count=2, interval=0.2):
    """
    Calls set_keyboard_color to make the keyboard blink in two different colors
    """
    for i in range(count):
        set_keyboard_color(color1)
        time.sleep(interval)
        set_keyboard_color(color2)
        time.sleep(interval)

#Notifications management functions

def notification_event(bus, message):
    """
    Function to be called by the dbus scanner
    Updates the 'NOTIFY' global variable with last notification name
    """
    global NOTIFY
    NOTIFY=message.get_args_list()[0]

def notification_scanner():
    """
    Starts dbus mainloop and listens for notifications
    When a notification is detected, calls notification_event
    """
    DBusGMainLoop(set_as_default=True)
    bus = SessionBus()
    bus.add_match_string_non_blocking("eavesdrop=true, interface='org.freedesktop.Notifications', member='Notify'")
    bus.add_message_filter(notification_event)
    mainloop = MainLoop()
    mainloop.run()

def parse_notification_settings_from_xml(path):
    """
    Parses notification settings from an XML file into a dictionary list
    Interval is expressed in seconds
    XML file example:
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
    	    <interval>0.5</interval>
	    </notification>
    </notifications>
    """
    #Setup variables
    global NOTIFICATION_SETTINGS_MANDATORY_ATTRIBUTES
    out_list = list()
    for notification_settings_node in xml_parser.parse(path).iterfind('notification'): 
        notification_settings_object = dict() #Will contain all attributes
        #Assign object's values from XML element
        for element in notification_settings_node:
            if element.tag == "name":
                notification_settings_object["name"] = element.text
            elif element.tag == "color":
                notification_settings_object["color"] = tuple(map(int, element.text.split(",")))
            elif element.tag == "count":
                notification_settings_object["count"] = int(element.text)
            elif element.tag == "interval":
                notification_settings_object["interval"] = float(element.text)
        #Check if object has all required keys
        for attribute in NOTIFICATION_SETTINGS_MANDATORY_ATTRIBUTES:
            if not (attribute in notification_settings_object):
                raise ValueError("Missing element in notification settings XML: " + attribute)
        #Appends checked element to notification settings list
        out_list.append(notification_settings_object.copy())
    #Returns filled list    
    return out_list
    
#Main

if __name__ == "__main__":
    #Setup argparse
    argparser = argparse.ArgumentParser(description = "Logitech Keyboard CPU meter")
    argparser.add_argument("-verbose", type = int, nargs = '?', const = 1, default = 0, help = "Text output")
    argparser.add_argument("-persistent", type = int, nargs = '?', const = 1, default = 0, help = "Keep running if keyboard disconnected")
    argparser.add_argument("-notify", type = int, nargs = '?', const = 1, default = 0, help = "Enable notification blink")
    args=argparser.parse_args()
    #Setup variables
    cpu_load_cache = [50] * SAMPLES
    current_sampling = 0
    notification_settings_list = list()
    #Starts dbus notifications scanner daemon, if requested
    if args.notify:
        try:
            notification_settings_list = parse_notification_settings_from_xml(NOTIFICATION_SETTINGS_FILE)
            threading.Thread(target = notification_scanner, daemon = True).start()   
        except Exception as e:
            print("Error in executing notification monitoring setup; check notification setting file")
            print(repr(e))
            exit()
    #Main loop
    while True:    
        if NOTIFY=="": #If no notification present, sets color based on CPU load
            #Updates CPU load cache
            cpu_load_cache[current_sampling] = (int(psutil.cpu_percent()))
            current_sampling+=1
            if current_sampling >= len(cpu_load_cache):
                current_sampling = 0
            #Gets current load (average from cache) and corresponding RGB value
            cpu_load = sum(cpu_load_cache) / len(cpu_load_cache)
            meter_color = get_load_color(cpu_load)
            #Sets keyboard color and sleeps for sampling time
            set_keyboard_color(meter_color, args.persistent) 
            #Prints output, if requested
            if args.verbose:
                os.system("clear")
                print("G Series Keyboard control")
                print("R: {:3} G: {:3} B: {:3}".format(*meter_color))
                print("CPU LOAD: {:.2f}%".format(cpu_load))
            #Sleeps for sampling time
            time.sleep(SAMPLING)
        else: #If notification present; executes notification blink (if notification is defined)
            if args.verbose:
                print("Notification active: " + NOTIFY)
            for notification in notification_settings_list:
                if NOTIFY==notification["name"]:
                    notification_blink(notification["color"], meter_color,notification["count"], notification["interval"])
                    break
            NOTIFY="" #Empties last notification name variable       