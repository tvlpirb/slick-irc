#!/usr/bin/python3
# Author: Talhah Peerbhai
# Email: hello@talhah.tech
import socket
import threading
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
            connects to an IRC server
        login(NICK,USER,RNAME=None)
            login to the server with these details
        join(channel,key=None)
            join a channel, possibly a secured one
        part(channel)
            part from a channel
        privmsg(who,msg)
            send a message to a channel or individual
        quitC(msg=None)
            quit and send a message
    '''
    # Initialise a socket connection and also the default HOST and PORT
    # which are set to 127.0.0.1:6667
    def __init__(self):
        '''
        Constructor for IrcCon class, initializes the socket, default host,
        port, nick, user and realname. Sets connected to False
        '''
        # https://docs.python.org/3/library/socket.html
        # AF_INET is for ipv4 IPS and domains, SOCK_STREAM is socket type,
        # in this case a constant two way TCP socket.
        self.sckt = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.HOST = "127.0.0.1" # default irc server
        self.PORT = 6667 # default plaintext port
        self.NICK = ""
        self.USER = ""
        self.RNAME = ""
        self.connected = False

    def connect(self,HOST=None,PORT=None):
        '''
        Connects to the IRC server, if sucessful starts receive loop in a
        thread.

        Parameters:
        -----------
        HOST : str
            The server URL or IP address, only supports IPv4, defaults to
            localhost
        PORT : int
            The port to connect to, defaults to 6667
        
        Calls:
        ------
        self.on_connect() : func
            Called upon sucessful connection to server
        self.on_error("ConnectionRefusedError")
            Called if cannot reach server
        '''
        # Non-default HOST and PORT
        if not HOST:
            self.HOST = HOST
        if not PORT:
            self.PORT = PORT
        try:
            self.sckt.connect((self.HOST,self.PORT))
            self.connected = True
            self.on_connect()
            thread = threading.Thread(target=self.recv_loop,args=[self.sckt]) 
            thread.daemon = True
            thread.start() 
        except:
            self.on_error("ConnectionRefusedError")
    
    def recv_loop(self,con):
        '''
        Receive loop to receive incoming messages

        Parameters:
        -----------
        con : socket
            The socket which is receiving incoming messages
        '''
        while True:
            # Check if there is any data on socket, timeout after 0.1s
            # prevent unecessary socket.recv
            (r,wx,error) = select([con], [], [con], 0.1)
            # Data to read
            if r:
                buffer = ""
                buffer += buffer+self.sckt.recv(1024).decode("UTF-8")
                temp = buffer.split("\n")
                # We need to pop last element as when we receive data it has
                # \r\n and we are splitting by \n, so we'd go from "hello\r\n"
                # to ["hello\r",""] and that last element needs to be ignored
                temp.pop(-1)
                for line in temp:
                    line = line.rstrip()
                    line = line.split()
                    self.incoming(line)
 
    def login(self,NICK,USER,RNAME=None):
        '''
        Login to the IRC server

        Parameters:
        -----------
        NICK : str
            The desired nick
        USER : str
            The desired username
        RNAME : str
            Real name of user, defaults to nick
        '''
        self.NICK = NICK
        self.USER = USER
        # If a real name specified
        if RNAME:
            self.RNAME = RNAME
        else:
            self.RNAME = NICK
        if self.connected:
            self.sckt.send(bytes(f"NICK {self.NICK}\r\n","UTF-8"))
            self.sckt.send(bytes(f"USER {USER} {USER} {USER}: {RNAME}\r\n","UTF-8"))
        else:
            self.on_error("ConnectionRefusedError")
    
    def incoming(self,line):
        '''
        Process incoming messages
        '''
        try:
            # Handle pinging
            if line[0] == "PING":
                print("PONGED SERVER")
                self.sckt.send(bytes(f"PONG {line[1]}\r\n","UTF-8"))
            elif self.NICK + "!" in line[0]:
                # Ignore things such as
                # :test3!~u@szawf88ssv98q.irc JOIN #test
                pass
            elif line[1] == "401":
                # :server 401 NICK INVALIDNICK :No such nick
                pass
            elif line[1] == "403":
                # :server 403 NICK INVALIDCHAN :N such channel
                pass
            elif line[1] == "433":
                # :server 433 * AttemptedNICK :Nickname is already in use
                pass
            elif line[1] == "PRIVMSG":
                # :test1!~u@szawf88ssv98q.irc PRIVMSG talhah :hello
                # :test2!~u@szawf88ssv98q.irc PRIVMSG #test :hello
                who = line[0].split("!")
                who = who[0].lstrip(":")
                channel = line[2]
                msg = line[3:].lstrip(":")
                self.on_message(who,channel,msg)
            elif line[1] == "NOTICE":
                # :talhah.test NOTICE test3 :Server is shutting down
                # :*.joseon.kr NOTICE * :*** You must use TLS/SSL and authenticate via SASL 
                notice = ' '.join(line[3:])
                notice = notice.lstrip(":")
                if notice == "Server is shutting down":
                    self.on_server_shutdown()
                if "You must use TLS/SSL" in notice:
                    self.on_error("SSLRequired")
            else:
                line = ' '.join(line)
                self.unknown_message(line) 
        except:
            line = ' '.join(line)
            self.unknown_message(line)

    # Join a channel 
    def join(self,channel,key=None):
        if key:
            self.sckt.send(bytes(f"JOIN {channel} {key}\r\n","UTF-8"))
        self.sckt.send(bytes(f"JOIN {channel}\r\n","UTF-8"))

    # Part a channel
    def part(self,channel):
        self.sckt.send(bytes(f"PART {channel}\r\n","UTF-8"))

    # Message an individual or channel
    def privmsg(self,who,msg):
        self.sckt.send(bytes(f"PRIVMSG {who} :{msg}\r\n","UTF-8"))
    
    # Indicate to server that client is quitting
    def quitC(self,msg=None):
        if not msg:
            msg = self.NICK
        self.sckt.send(bytes(f"QUIT :{msg}","UTF-8"))
    
    def on_connect(self):
        pass

    def on_error(self,errorType):
        pass
    
    # Called on message
    def on_message(self,who,channel,msg):
        pass

    def unknown_message(self,line):
        pass
    
    def on_server_shutdown(self):
        pass