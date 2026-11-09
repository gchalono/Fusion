"""FNXC:BlockerResolution 2026-11-09-18:27:
SYNTHETIC protocol-specific positive controls, entirely in a disposable trusted
network/user namespace with no external route. Temporary capabilities exist only
there; the untrusted coding sandbox and its seccomp/capability policy are unchanged.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import threading


def inside():
    subprocess.run(['ip','link','set','lo','up'],check=True)
    for address in ('169.254.169.254/32','192.0.2.53/32'):
        subprocess.run(['ip','addr','add',address,'dev','lo'],check=True)
    route=Path('/proc/net/route').read_text()
    assert not any(line.split()[1]=='00000000' for line in route.splitlines()[1:]),'external_route'
    results={}
    for name,family,address in (('metadata',socket.AF_INET,'169.254.169.254'),('ipv6',socket.AF_INET6,'::1')):
        with socket.socket(family) as server:
            server.bind((address,0));server.listen()
            with socket.socket(family) as client:
                client.settimeout(2);client.connect((address,server.getsockname()[1]));peer,_=server.accept()
                with peer:client.sendall(b'SYNTHETIC');results[name]=peer.recv(32)==b'SYNTHETIC'
    # A real DNS wire query/response through the same UDP protocol and port 53.
    query=struct.pack('!HHHHHH',0x2a2a,0x0100,1,0,0,0)+b'\x09synthetic\x07invalid\0'+struct.pack('!HH',1,1)
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as server:
        server.bind(('192.0.2.53',53))
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as client:
            client.settimeout(2);client.sendto(query,server.getsockname());packet,peer=server.recvfrom(512)
            server.sendto(packet[:2]+b'\x81\x80'+packet[4:],peer);answer,_=client.recvfrom(512)
            results['dns']=packet==query and answer[:4]==b'\x2a\x2a\x81\x80'
    # Raw ICMP echo creation and loopback reply, not an HTTP substitute.
    packet=struct.pack('!BBHHH',8,0,0,123,1)+b'SYNTHETIC'
    if len(packet)%2:packet+=b'\0'
    words=struct.unpack('!'+str(len(packet)//2)+'H',packet);checksum=sum(words)
    while checksum>>16:checksum=(checksum&65535)+(checksum>>16)
    packet=packet[:2]+struct.pack('!H',(~checksum)&65535)+packet[4:]
    with socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_ICMP) as client:
        client.settimeout(2);client.sendto(packet,('127.0.0.1',0));results['raw']=False
        for _ in range(4):
            reply,_=client.recvfrom(512);offset=(reply[0]&15)*4
            if reply[offset]==0 and reply[offset+4:offset+8]==packet[4:8]:results['raw']=True;break
    assert all(results.values()),results
    print(json.dumps({'classification':'SYNTHETIC','positive_controls':results,'external_route':False}))


def main():
    p=argparse.ArgumentParser();p.add_argument('--inside',action='store_true');a=p.parse_args()
    if a.inside:inside();return
    command=['bwrap','--unshare-user','--unshare-net','--unshare-pid','--uid','0','--gid','0','--cap-add','CAP_NET_ADMIN','--cap-add','CAP_NET_RAW','--cap-add','CAP_NET_BIND_SERVICE','--die-with-parent','--ro-bind','/','/','--proc','/proc','--clearenv','--setenv','PATH',os.environ['PATH'],'--',sys.executable,'-B',str(Path(__file__).resolve()),'--inside']
    subprocess.run(command,check=True,timeout=20,env={'PATH':os.environ['PATH']},close_fds=True)
if __name__=='__main__':main()
