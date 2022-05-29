import os, sys, time, threading
import logging
import importlib
import pywifi
from hw_find import get_cpu_serial_number
import RPi.GPIO as GPIO

log_file_path = "/boot/hiwonder_wifi.log"
config_file_name = "hiwonder_wifi_conf.py"
internal_config_file_dir_path = "/etc/Hiwonder"
external_config_file_dir_path = "/boot"
internal_config_file_path = os.path.join(internal_config_file_dir_path, config_file_name)
external_config_file_path = os.path.join(external_config_file_dir_path, config_file_name)
led_on_time = 100
led_off_time = 100

led1_pin = 16
led2_pin = 26

def update_globals(module):
    if module in sys.modules:
        mdl = importlib.reload(sys.modules[module])
    else:
        mdl = importlib.import_module(module)
    if "__all" in mdl.__dict__:
        names = mdl.__dict__["__all__"]
    else:
        names = [x for x in mdl.__dict__ if not x.startswith("_")]
    globals().update({k: getattr(mdl, k) for k in names})


def check_dependens(logger):
    exit_ = False
    if os.system("hostapd -v > /dev/null 2>&1") != 256:
        logger.error("hostapd not installed")
        exit_ = True
    if os.system("ip a > /dev/null 2>&1") != 0:
        logger.error("iproute2 not installed")
        exit_ = True
    if os.system("dnsmasq --version > /dev/null 2>&1") != 0:
        logger.error("dnsmasq not installed")
        exit_ = True
    if os.system("iw > /dev/null 2>&1") != 0:
        logger.error("iw not installed")
        exit_ = True
    if os.system("create_ap --version > /dev/null 2>&1") != 0:
        logger.error("create_ap not installed")
        exit_ = True
    if os.system("haveged > /dev/null 2>&1") != 0:
        logger.error("haveged not installed")
        exit_ = True
    if exit_ is True:
        sys.exit(-1)

def led_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(led1_pin, GPIO.OUT)
    GPIO.output(led1_pin, 1)
    GPIO.setup(led2_pin, GPIO.OUT)
    GPIO.output(led2_pin, 0)

def led_thread():
    global led_on_time
    global led_off_time
    local_led_on_time = 0
    local_led_off_time = 0

    count = 0
    cycle_time = 0
    while True:
        if local_led_on_time != led_on_time or local_led_off_time != led_off_time:
            local_led_on_time = led_on_time
            local_led_off_time = led_off_time
            cycle_time = local_led_on_time + local_led_off_time
            count = 0
        if count < local_led_on_time:
            GPIO.output(led1_pin, 0)
            count += 1
        elif count < cycle_time:
            GPIO.output(led1_pin, 1)
            count += 1
        else:
            count = 0

        time.sleep(0.01)

if __name__ == "__main__":

    sn = get_cpu_serial_number()   #get cpu serial number
    led_setup()
    HW_WIFI_MODE = 1  #1 means AP mode, 2 means Client Mode, 3 means AP mode with eth0 internet share '
    HW_WIFI_AP_SSID = ''.join(["HW-", sn[0:8]])
    HW_WIFI_STA_SSID = ""
    HW_WIFI_AP_PASSWORD = ""
    HW_WIFI_STA_PASSWORD = ""
    HW_WIFI_AKM_TYPE = pywifi.const.AKM_TYPE_WPA2PSK
    HW_WIFI_CIPHER_TYPE = pywifi.const.CIPHER_TYPE_CCMP
    HW_WIFI_CHANNEL = 7 #149 153  157 161
    HW_WIFI_AP_GATEWAY = "192.168.149.1"
    HW_WIFI_COUNTRY = "US"
    HW_WIFI_FREQ_BAND = 2.4 
    HW_WIFI_TIMEOUT = 30
    HW_WIFI_RESET_NOW = False
    HW_WIFI_LED = True

    logger = logging.getLogger("Hiwonder WiFi tool")
    logger.setLevel(logging.DEBUG)
    log_handler = logging.FileHandler(log_file_path)
    log_handler.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(name)s - %(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)

    ### check dependen
    check_dependens(logger)

    ### read config file
    if os.path.exists(config_file_name):
        update_globals(os.path.splitext(config_file_name)[0])
    if os.path.exists(internal_config_file_path):
        sys.path.insert(1, internal_config_file_dir_path)
        update_globals(os.path.splitext(config_file_name)[0])
    if os.path.exists(external_config_file_path):
        sys.path.insert(0, external_config_file_dir_path)
        update_globals(os.path.splitext(config_file_name)[0])

    if HW_WIFI_RESET_NOW == True:
        os.system("rm " + config_file_name + " > /dev/null 2>&1")
        os.system("rm " + internal_config_file_path + " > /dev/null 2>&1")
        os.system("rm " + internal_config_file_dir_path + "/__pycache__  -rf > /dev/null 2>&1")
        os.system("rm " + external_config_file_path + " > /dev/null 2>&1")
        os.system("rm " + external_config_file_dir_path + "/__pycache__  -rf > /dev/null 2>&1")
        HW_WIFI_MODE = 1  
        HW_WIFI_AP_SSID = ''.join(["HW-", sn[0:8]])
        HW_WIFI_STA_SSID = ""
        HW_WIFI_AP_PASSWORD = ""
        HW_WIFI_STA_PASSWORD = ""
        HW_WIFI_CHANNEL = 7
        HW_WIFI_AP_GATEWAY = "192.168.149.1"
        HW_WIFI_COUNTRY = "US"
        HW_WIFI_FREQ_BAND = 2.4 

    def WIFI_MGR():
        global HW_WIFI_AP_SSID
        global HW_WIFI_STA_SSID
        global HW_WIFI_AP_PASSWORD
        global HW_WIFI_STA_PASSWORD
        global led_on_time
        global led_off_time
        if HW_WIFI_MODE == 1: #AP
            led_on_time = 50
            led_off_time = 50
            os.system("set +o history > /dev/null 2>&1")
            os.system("pkill create_ap > /dev/null 2>&1")
            os.system("pkill hostapd > /dev/null 2>&1")
            os.system("pkill wpa_supplicant > /dev/null 2>&1")
            if type(HW_WIFI_AP_PASSWORD) != str: #check password
                logger.error("Invalid HW_WIFI_PASSWORD")
                HW_WIFI_AP_PASSWORD = ""
            if len(HW_WIFI_AP_PASSWORD) < 8 and HW_WIFI_AP_PASSWORD != "":
                logger.error("password is too short")
                HW_WIFI_AP_PASSWORD = ""
            if type(HW_WIFI_AP_SSID) != str: #check ssid
                logger.error("Invalid HW_WIFI_AP_SSID")
                HW_WIFI_AP_SSID = ''.join(["HW-", sn[0:8]])
            cmd = ''.join(["create_ap -n wlan0 --no-virt -g ", HW_WIFI_AP_GATEWAY ,  " --country ", HW_WIFI_COUNTRY, " --freq-band ", str(HW_WIFI_FREQ_BAND), " -c ", str(HW_WIFI_CHANNEL), " ", HW_WIFI_AP_SSID," ", HW_WIFI_AP_PASSWORD])
            print(cmd)
            t = threading.Thread(target = lambda :os.system(cmd), daemon=True)
            logger.info("Create AP:" + HW_WIFI_AP_SSID)
            t.start()
            os.system("set -o history > /dev/null 2>&1")
            t.join()
            return -1

        elif HW_WIFI_MODE == 2: #Client
            led_on_time = 5
            led_off_time = 5
            os.system("set +o history > /dev/null 2>&1")
            os.system("pkill create_ap > /dev/null 2>&1")
            os.system("pkill hostapd > /dev/null 2>&1")
            os.system("pkill wpa_supplicant > /dev/null 2>&1")
            logger.info("Connecting to " + HW_WIFI_STA_SSID)
            t = threading.Thread(target = lambda :os.system("wpa_supplicant -iwlan0 -C /var/run/wpa_supplicant"), daemon=True)
            t.start()
            os.system("set -o history > /dev/null 2>&1")
            time.sleep(2)

            profile = pywifi.Profile()
            profile.auth = pywifi.const.AUTH_ALG_OPEN
            profile.akm.append(HW_WIFI_AKM_TYPE)
            profile.cipher = HW_WIFI_CIPHER_TYPE
            profile.ssid = HW_WIFI_STA_SSID
            profile.key = HW_WIFI_STA_PASSWORD

            wifi = pywifi.PyWiFi()
            iface = wifi.interfaces()[1]
            iface.remove_all_network_profiles()
            tmp_profile = iface.add_network_profile(profile)
            iface.connect(tmp_profile)

            count = 0
            while True:
                if count < HW_WIFI_TIMEOUT and iface.status() != pywifi.const.IFACE_CONNECTED:
                    count += 1
                    time.sleep(1)
                elif iface.status() == pywifi.const.IFACE_CONNECTED:
                    msg = "Connected to " + HW_WIFI_STA_SSID
                    logger.info(msg)
                    threading.Thread(target= lambda: os.system("dhclient wlan0"), daemon=True).start()
                    led_on_time = 100
                    led_off_time = 0
                    break
                else:
                    msg = "Can not connect to SSID: " + HW_WIFI_STA_SSID
                    logger.error(msg)
                    return 0

            t.join()
            return -1
        else:
            logger.error("Invalid HW_WIFI_MODE")
    if HW_WIFI_LED == True:
        threading.Thread(target = led_thread, daemon=True).start()
    while True:
        ret = WIFI_MGR()
        if ret == -1:
            sys.exit(0)
        HW_WIFI_MODE = 1  #1 means AP mode, 2 means Client Mode, 3 means AP mode with eth0 internet share '
        HW_WIFI_AP_SSID = ''.join(["HW-", sn[0:8]])
        HW_WIFI_AP_PASSWORD = ""
