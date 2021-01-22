import select
import socket
import random
import struct
from threading import Timer
import tkinter


class BOOTPHeader(object):
    OPC_REQUEST = b'\x01'
    OPC_REPLY = b'\x02'

    def __init__(self, opcode, mac):
        assert opcode == self.OPC_REQUEST or opcode == self.OPC_REPLY, "Invalid opcode"

        self.opcode = opcode
        self.hardware_type = b'\x01'
        self.hardware_address_length = b'\x06'
        self.hop_count = b'\x00'
        self.transaction_id = self.gen_transaction_id()
        self.no_of_seconds = b'\x00\x00'
        self.flags = b'\x80\x00'
        self.client_ip = b'\x00\x00\x00\x00'
        self.your_ip = b'\x00\x00\x00\x00'
        self.server_ip = b'\x00\x00\x00\x00'
        self.gateway_ip = b'\x00\x00\x00\x00'
        self.client_hardware_address = mac + b'\x00' * 10  # 10 octeti padding
        self.server_host_name = b'\x00' * 64
        self.boot_filename = b'\x00' * 128
        self.vendor_specific_info = self.options = ''

    def gen_transaction_id(self):
        return random.randbytes(4)

    def ip_to_int(self, ip):
        l = ip.split('.')
        return select.pack('cccc', l)

    def set_client_ip(self, ip):
        if type(ip) == str:
            self.client_ip = self.ip_to_int(ip)
        elif type(ip) == int:
            self.client_ip = ip

    def pack(self):
        # pformat = 'cccc4s2s2s4s4s4s4s16s64s128s'+str(len(self.options))+'s'
        # print(pformat)
        # return struct.pack(pformat,
        #    self.opcode, self.hardware_type, self.hardware_address_length,
        #    self.hop_count, self.transaction_id, self.no_of_seconds, self.flags, self.client_ip,
        #    self.your_ip, self.server_ip, self.gateway_ip, self.client_hardware_address,
        #    self.server_host_name, self.boot_filename, self.options)
        return b''.join([self.opcode, self.hardware_type, self.hardware_address_length,
                         self.hop_count, self.transaction_id, self.no_of_seconds, self.flags, self.client_ip,
                         self.your_ip, self.server_ip, self.gateway_ip, self.client_hardware_address,
                         self.server_host_name, self.boot_filename, self.options])


class DHCPPacket(BOOTPHeader):
    TYPE_DISCOVER = b'\x01'
    TYPE_OFFER = b'\x02'
    TYPE_REQUEST = b'\x03'
    TYPE_ACK = b'\x05'

    OP_SUBNETMASK = b'\x01'  # opt 1
    OP_ROUTER = b'\x03'  # opt 3
    OP_DNS = b'\x06'  # opt 6
    OP_MESSAGE_TYPE = b'\x35'  # opt 53
    OP_SERVER_ID = b'\x36'  # opt 54
    OP_CLIENT_ID = b'\x3d'  # opt 61
    OP_REQUESTED_IP = b'\x32'  # opt 50
    OP_PARAM_REQ_LIST = b'\x37'  # opt 55
    OP_END = b'\xff'  # opt 255

    def __init__(self, dhcptype, mac):
        if dhcptype == self.TYPE_DISCOVER or dhcptype == self.TYPE_REQUEST:
            opcode = BOOTPHeader.OPC_REQUEST
        elif dhcptype == self.TYPE_OFFER or dhcptype == self.TYPE_ACK:
            opcode = BOOTPHeader.OPC_REPLY

        super(DHCPPacket, self).__init__(opcode, mac)

        self.option_list = []
        self.add_option(self.OP_MESSAGE_TYPE, dhcptype)

    def add_option(self, option, *args):
        value = b''
        length = 0
        for i in args:
            length += len(i)
            value += i
        if length > 0:
            length = bytes([length])
        else:
            length = b''
        self.option_list.append(option + length + value)

    def pack(self):
        self.add_option
        self.options = b'\x63\x82\x53\x63'  # Magic cookie

        self.options += b''.join(self.option_list)

        # Adauga la sfarsit optiunea END
        self.options += DHCPPacket.OP_END
        return super(DHCPPacket, self).pack()

    def unpack(self, data):

        # TODO:
        # 1. Procesare pachet si creare dictionar cu optiuni + date
        # self.opcode = data[0:1]
        # self.hardware_type = data[1:2]
        self.opcode, self.hardware_type, self.hardware_address_length, \
        self.hop_count, self.transaction_id, self.no_of_seconds, self.flags, self.client_ip, \
        self.your_ip, self.server_ip, self.gateway_ip, self.client_hardware_address, \
        self.server_host_name, self.boot_filename, self.options \
            = struct.unpack('cccc4s2s2s4s4s4s4s16s64s128s' + str(len(data) - 236) + 's', data)

        self.opt_dict = {}
        idx = 4
        print(self.options)
        while True:
            op_code = self.options[idx]
            if op_code == 255:
                self.opt_dict[op_code] = ''
                break
            op_len = self.options[idx + 1]
            op_data = self.options[idx + 2:idx + 2 + op_len]
            idx = idx + 2 + op_len
            self.opt_dict[op_code] = op_data
            print("Optiunea " + str(op_code)+" : "+str(op_data))


def renew(client_id, server_id, *args):
    ren = DHCPPacket(DHCPPacket.TYPE_REQUEST, b'\x9c\xb7\x0d\x69\x71\x8d')
    ren.add_option(DHCPPacket.OP_CLIENT_ID, client_id)
    ren.add_option(args)

    print("trimitere request renewal")
    s.sendto(ren.pack(), (server_id, 67))


# Creare socket UDP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
# Activare optiune transmitere pachete de difuzie
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# Activare optiune refolosire port (portul 68 este folosit si de clientul DHCP al SO-ului)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Asociere interfata + port (sub Windows nu este permisa transmisia prin difuzie pe toate interfetele,
# deci trebuie specificata adresa IP asociata unei interfete... de unde si necesitatea adreselor APIPA)
s.bind(('192.168.100.8', 68))

# Creare pachet Discover
p = DHCPPacket(DHCPPacket.TYPE_DISCOVER, b'\x9c\xb7\x0d\x69\x71\x8d')
# Adaugare optiuni
p.add_option(DHCPPacket.OP_CLIENT_ID, b'\x01', b'\x9c\xb7\x0d\x69\x71\x8d')
p.add_option(DHCPPacket.OP_REQUESTED_IP, b'\x00\x00\x00\x00')
p.add_option(DHCPPacket.OP_PARAM_REQ_LIST, DHCPPacket.OP_SUBNETMASK, DHCPPacket.OP_ROUTER, DHCPPacket.OP_DNS)

print("S-a trimis pachetul Discover")
s.sendto(p.pack(), ('255.255.255.255', 67))

# Apelam la functia sistem IO -select- pentru a verifca daca socket-ul are date in bufferul de receptie
# Stabilim un timeout de 3 secunde
r, _, _ = select.select([s], [], [], 3)
if not r:
    print("Nu s-a receptionat un raspuns de la server")
else:
    # S-a receptioneaza un pachet de date pe portul 68
    dr = s.recv(1024)
    p1 = DHCPPacket(DHCPPacket.TYPE_OFFER, b'')
    p1.unpack(dr)
    print("S-a receptionat pachetul OFFER\n")

    p2 = DHCPPacket(DHCPPacket.TYPE_REQUEST, b'\x9c\xb7\x0d\x69\x71\x8d')

    p2.add_option(DHCPPacket.OP_CLIENT_ID, p1.hardware_type, p1.client_hardware_address)
    p2.add_option(DHCPPacket.OP_REQUESTED_IP, p1.your_ip)
    p2.add_option(DHCPPacket.OP_SERVER_ID, p1.opt_dict[54])
    p2.add_option(DHCPPacket.OP_PARAM_REQ_LIST, DHCPPacket.OP_SUBNETMASK, DHCPPacket.OP_ROUTER, DHCPPacket.OP_DNS)

    print("S-a trimis pachetul Request")
    s.sendto(p2.pack(), ('255.255.255.255', 67))

    r1, _, _ = select.select([s], [], [], 3)
    if not r1:
        print("Nu s-a receptionat un raspuns de la server")
    else:
        # S-a receptioneaza un pachet de date pe portul 68
        dr1 = s.recv(1024)
        p3 = DHCPPacket(DHCPPacket.TYPE_ACK, b'')
        p3.unpack(dr1)
        print("S-a receptionat ack")

        while 1:
            Timer(int.from_bytes(p3.opt_dict[51], "big")/2, renew, (p3.OP_CLIENT_ID, p3.OP_SERVER_ID,
                                                                    DHCPPacket.OP_PARAM_REQ_LIST,
                                                                    DHCPPacket.OP_SUBNETMASK, DHCPPacket.OP_ROUTER,
                                                                    DHCPPacket.OP_DNS)).start()
            r2, _, _ = select.select([s], [], [], 3)
            if not r2:
                print("Nu s-a receptionat un raspuns de la server")
                break
            else:
                # S-a receptioneaza un pachet de date pe portul 68
                dr2 = s.recv(1024)
                p4 = DHCPPacket(DHCPPacket.TYPE_ACK, b'')
                p4.unpack(dr2)

# TODO:
# 1. Procesare pachet OFFER si afisare optiuni
# 2. Generare pachet REQUEST
# 3. Procesare pachet ACK
