import os, sys
import socketserver
import json

class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(2)
        count = 0
        data = None
        while True:
            try:
                if data is None:
                    data = self.request.recv(1024)
                else:
                    data += self.request.recv(1024)
                if not data:
                    pass
                else:
                    msg = str(data, encoding='utf-8')
                    try:
                        key_dict = json.loads(msg)
                    except:
                        continue
                    print(key_dict)
                    if 'setwifi' in key_dict:
                        key_dict = key_dict['setwifi']
                        if 'ssid' in key_dict and 'passwd' in key_dict:
                            buf = "HW_WIFI_MODE = 2\n"
                            buf += "HW_WIFI_STA_SSID = \"" + key_dict['ssid'] + '\"\n'
                            buf += "HW_WIFI_STA_PASSWORD = \"" + key_dict['passwd'] + '\"\n'
                            with open("/etc/Hiwonder/hiwonder_wifi_conf.py", "w") as fp:
                                fp.write(buf)
                            print(buf)
                            os.system("systemctl restart hw_wifi.service")
                    break
            except:
                break
        self.request.close()

class PhoneServer(socketserver.TCPServer):
    timeout = 2
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)

    def handle_timeout(self):
        print('Timeout')

if __name__ == "__main__":
    if not os.path.exists("/etc/Hiwonder"):
        os.system("mkdir /etc/Hiwonder")
    server = PhoneServer(('0.0.0.0', 9026), TCPHandler)
    server.serve_forever()
