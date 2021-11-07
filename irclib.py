#!/usr/bin/python3
# Author: Talhah Peerbhai
# Email: hello@talhah.tech
import socket
import threading
import time
from select import select

class IrcCon(object):
    '''
    Implement the IRC protocol see below for specifications:
        https://datatracker.ietf.org/doc/html/rfc1459 (1993) # Core
        https://datatracker.ietf.org/doc/html/rfc2812 (2000) # Core
        https://datatracker.ietf.org/doc/html/rfc7194 (2014)
        https://ircv3.net/irc/ (present) IRCv3 spec
    
    Methods:
        connect(HOST,PORT)
            - HOST=127.0.0.1 default
            - PORT=6667 default
    '''
    # Initialise a socket connection and also the default HOST and PORT
    # which are set to 127.0.0.1:6667
    def __init__(self):
        # https://docs.python.org/3/library/socket.html
        # AF_INET is for ipv4 IPS and domains, SOCK_STREAM is socket type,
        # in this case a constant two way TCP socket.
        self.sckt = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.HOST = "127.0.0.1" # default irc server
        self.PORT = 6667 # default plaintext port
        self.NICK = ""
        self.connected = False

    def on_error(self,errorType):
        pass
    
    # Connect to IRC server
    def connect(self,HOST=None,PORT=None):
        # Non-default HOST and PORT
        if not HOST:
            self.HOST = HOST
        if not PORT:
            self.PORT = PORT
        try:
            self.sckt.connect((self.HOST,self.PORT))
            self.connected = True
            thread = threading.Thread(target=self.recv_loop,args=[self.sckt]) 
            thread.daemon = True
            thread.start() 
        except:
            self.on_error("ConnectionRefusedError")
    
    def recv_loop(self,con):
        while True:
            # Check for data every 0.1 seconds, otherwise timeout
            (r,wx,e) = select([con],[],[con],0.1)
            # There is data available
            if r: 
                buffer = ""
                buffer += self.sckt.recv(2048).decode("UTF-8")
                temp = buffer.split("\n")
                for line in temp:
                    line = line.rstrip()
                    print(line)
            
    def login(self,NICK,USER,RNAME):
        self.NICK = NICK
        self.sckt.send(bytes(f"NICK {self.NICK}\r\n","UTF-8"))
        self.sckt.send(bytes(f"USER {USER} {USER} {USER}: {RNAME}\r\n","UTF-8"))
 