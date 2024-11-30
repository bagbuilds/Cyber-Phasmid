import RPi.GPIO as GPIO
import time
import os

# Configuration variables
INTERFACE_WIFI = "wlan0"  # Replace with your Wi-Fi interface name
GPIO_PIN = 22             # Replace with the GPIO pin you're using

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Needed only if interface is not in unmanaged mode. Has no effect otherwise
#def wifi_on():
#    # Enable the WiFi interface
#    os.system(f"/sbin/ifconfig {INTERFACE_WIFI} up")

#def wifi_off():
#    # Disable the WiFi interface
#    os.system(f"/sbin/ifconfig {INTERFACE_WIFI} down")

def hostapd_on():
    # Start the hostapd service
    os.system("systemctl start hostapd")

def hostapd_off():
    # Stop the hostapd service
    os.system("systemctl stop hostapd")

def main():
    previous_state = None

    while True:
        current_state = GPIO.input(GPIO_PIN)
        if current_state != previous_state:
            previous_state = current_state
            if current_state == GPIO.HIGH:
                # Switch is ON
                hostapd_on()
                #wifi_on()
                #print("WiFi and hostapd have been enabled.")
            else:
                # Switch is OFF
                hostapd_off()
                #wifi_off()
                #print("WiFi and hostapd have been disabled.")
        time.sleep(0.1)

try:
    main()
except KeyboardInterrupt:
    GPIO.cleanup()
