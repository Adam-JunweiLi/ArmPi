import os
import sys
import getopt
import socket

def get_cpu_serial_number():
    f_cpu_info = open("/proc/cpuinfo")
    for i in f_cpu_info.readlines():
        if i.find('Serial',0, len(i)) == 0:
            serial_num = i.replace('\n', '')[::-1][0:16].upper()
    return serial_num

if __name__ == "__main__":
    host = '0.0.0.0'
    port = 9027
    robot_type = "SPIDER"
    sn = get_cpu_serial_number()
    try:
        opts, argsa = getopt.getopt(sys.argv[1:], "ht:a:p:", [])
    except getopt.GetoptError:
        print('test.py -t <robot type>')
        print('example: test.py -t SPIDER')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -t <robot type>')
            print('example: test.py -t SPIDER')
            sys.exit()
        elif opt == '-t':
            robot_type = arg
        elif opt == '-a':
            host = arg
        elif opt == '-p':
            port = int(arg)
        else:
            print(opt)
            print("unknow argument" + "\"" + str(opt) + "\"")
    addr = (host, port)
    udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpServer.bind(addr)
    sn = (get_cpu_serial_number() + "00000000000000000000000000")[:32]
    while True:
        data, addr = udpServer.recvfrom(1024)
        msg = str(data, encoding = 'utf-8')
        print(msg)
        if msg == "LOBOT_NET_DISCOVER":
            udpServer.sendto(bytes(robot_type +":" + sn + "\n", encoding='utf-8'),addr)
   
