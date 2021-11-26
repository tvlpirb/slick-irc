#!/usr/bin/python3
# Author: Talhah Peerbhai
# Email: hello@talhah.tech
import socket
import threading
from select import select
import ssl

class IrcCon(object):
    '''
    Implement the IRC protocol see below for specifications:
        https://datatracker.ietf.org/doc/html/rfc1459 (1993) # Core
        https://datatracker.ietf.org/doc/html/rfc2812 (2000) # Core
        https://datatracker.ietf.org/doc/html/rfc7194 (2014)
        https://ircv3.net/irc/ (present) IRCv3 spec
        https://www.alien.net.au/irc/irc2numerics.html # Numeric replies
    
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
        
        TODO Complete documentation
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
        self.channels = set()
        self.startWhoList = False
        self.startNames = False
        self.names = dict()
        self.userDone = False
        self.failedLogin = False

    def connect(self,HOST=None,PORT=None,SSL=False):
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
        if HOST != self.HOST:
            self.HOST = HOST
        if PORT != self.PORT:
            self.PORT = PORT
        try:
            if SSL:
                self.ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
                self.sckt = self.ctx.wrap_socket(self.sckt)
            self.sckt.connect((self.HOST,self.PORT))
            self.connected = True
            self.on_connect()
            self.thread = threading.Thread(target=self.recv_loop,args=[self.sckt]) 
            self.thread.daemon = True
            self.thread.start() 
            return True
        except:
            self.on_error("ConnectionRefusedError")
            self.connected = False
            return False

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
        if RNAME and RNAME != "":
            self.RNAME = RNAME
        else:
            self.RNAME = NICK
        if self.connected:
            self.sckt.send(bytes(f"NICK {self.NICK}\r\n","UTF-8"))
            # We haven't already submitted a username of client
            if not self.userDone:
                self.sckt.send(bytes(f"USER {self.USER} {self.USER} {self.USER}: {self.RNAME}\r\n","UTF-8"))
                self.userDone = True
            self.failedLogin = False
        else:
            self.on_error("ConnectionRefusedError")
    
    def incoming(self,line):
        '''
        Process incoming messages
        '''
        try:
            # Handle pinging
            if line[0] == "PING":
                self.sckt.send(bytes(f"PONG {line[1]}\r\n","UTF-8"))
            # Ignore things such as 
            # :test3!~u@szawf88ssv98q.irc JOIN #test
            elif self.NICK + "!" in line[0]:
                pass
            # Nick non existent in format:
            # :host 401 NICK ATTEMPTEDNICK :No such nick
            elif line[1] == "401":
                self.on_invalid_nick()
            # TODO Invalid channel
            # Channel non existent in format:
            # :host 403 NICK CHAN :No such channel
            elif line[1] == "403":
                pass
            # Nickname in use, format:
            # :host 443 * AttemptedNICK :Nickname is already in use
            elif line[1] == "433":
                self.on_error("NickInUse")
            # Private and channel message in format:
            # :nick!~username@hostname PRIVMSG NICK/CHAN :msg
            elif line[1] == "PRIVMSG":
                who = line[0].split("!")
                who = who[0].lstrip(":")
                channel = line[2]
                msg = ' '.join(line[3:])
                #msg = msg.lstrip(":")
                msg = msg[1:]
                self.on_message(who,channel,msg)
            elif "NickServ" in line[0]:
                line = line[3:]
                line = ' '.join(line)
                line = line[1:]
                self.on_nickserv(line)
            # Notice message in format:
            # :host NOTICE nick/chan :msg
            elif line[1] == "NOTICE":
                notice = ' '.join(line[3:])
                #notice.lstrip(":")
                notice = notice[1:]
                who = line[2]
                if who == self.NICK or who == "*":
                    self.on_notice("info",notice)
                else:
                    self.on_notice(who,notice)
            # Join message in format:
            # :nick!user@hostname JOIN chan
            # Note: it can also be :chan
            elif line[1] == "JOIN":
                who = line[0].split("!")
                hostname = who[1]
                who = who[0].lstrip(":")
                channel = line[2]
                channel = channel.lstrip(":")
                self.on_user_join(who,channel,hostname)
            # Part message in format:
            # :nick!user@hostname PART chan
            elif line[1] == "PART":
                who = line[0].split("!")
                hostname = who[1]
                who = who[0].lstrip(":")
                channel = line[2]
                channel = channel.lstrip(":")
                self.on_user_part(who,channel,hostname)
            # Nick message in format:
            # :nick!user@hostname NICK newnick
            elif line[1] == "NICK":
                #:talhah!~u@szawf88ssv98q.irc NICK test1
                who = line[0].split("!")
                hostname = who[1]
                who = who[0].lstrip(":")
                newNick = line[2]
                # Ignore our own name change
                if newNick != self.NICK:
                    self.on_user_nick_change(who,newNick)
            # Quit message in format:
            #:nick!user@hostname QUIT :Quit: Message
            elif line[1] == "QUIT":
                who = line[0].split("!")
                hostname = who[1]
                who = who[0].lstrip(":")
                if line[2] == ":Quit:":
                    msg = ' '.join(line[3:])
                else:
                    msg = ' '.join(line[2:])
                    msg.lstrip(":")
                self.on_user_quit(who,hostname,msg)
            elif line[1] == "311":
                self.startWhoList = True
                self.on_whois(line)
            elif self.startWhoList:
                self.on_whois(line)
            # End of whois list message in format:
            # :host 318
            elif line[1] == "318":
                self.startWhoList = False
            # End of names list message in format:
            # :host 366 nick chan :End of /NAMES list.
            elif "366" in line:
                self.startNames = False
                self.end_names(self.namesChan)
            # Names list message for a channel in format:
            # :host 353 nick = #chan :names
            # It's important to note the list may come as multiple 353 messages
            # so we need to build list and only stop once we get 366
            elif line[1] == "353" or self.startNames:
                if not self.startNames:
                    self.namesChan = line[4]
                self.startNames = True
                names = line[5:]
                if line[1] != "353":
                    names = line
                self.on_names(self.namesChan, names)
            # Topic message for a channel without topic:
            # :host 331 nick chan :No topic is set
            elif line[1] == "331":
                chan = line[3]
                self.on_topic(chan,"No topic is set")
            # Topic message for a channel in format:
            # :host 332 nick chan :topic
            elif line[1] == "332":
                chan = line[3]
                topic = ' '.join(line[4:])
                topic = topic[1:]
                self.on_topic(chan,topic)
            # Ignore RPL_TOPICTIME
            elif line[1] == "333":
                pass
            else:
                line = line[3:]
                line = ' '.join(line)
                if line.startswith(":"):
                    # Strip leading colon
                    line = line[1:]
                self.unknown_message(line) 
        # Sometimes we get IndexError
        except IndexError:
            line = line[3:]
            line = ' '.join(line)
            line = line[1:]
            self.unknown_message(line)

    # Join a channel 
    def join(self,channel,key=None):
        if key:
            self.sckt.send(bytes(f"JOIN {channel} {key}\r\n","UTF-8"))
        if channel in self.channels:
            self.on_error("AlreadyInChan")
        else:
            self.channels.add(channel)
        self.sckt.send(bytes(f"JOIN {channel}\r\n","UTF-8"))

    # Part a channel
    def part(self,channel):
        self.channels.remove(channel)
        self.sckt.send(bytes(f"PART {channel}\r\n","UTF-8"))

    # Message an individual or channel
    def privmsg(self,who,msg):
        self.sckt.send(bytes(f"PRIVMSG {who} :{msg}\r\n","UTF-8"))
    
    # Whois info for a user
    def whois(self,who):
        self.sckt.send(bytes(f"WHOIS {who}\r\n","UTF-8"))
    
    # Indicate to server that client is quitting
    def quitC(self,msg=None):
        if not msg:
            msg = self.NICK
        self.sckt.send(bytes(f"QUIT :{msg}\r\n","UTF-8"))

    # Reconnect to the IRC server
    def reconnect(self):
        self.sckt.shutdown(socket.SHUT_RDWR)
        self.sckt.close()
        self.sckt = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connected = False
        self.userDone = False
        self.connect(self.HOST,self.PORT)
        self.login(self.NICK,self.USER,self.RNAME)

    # Disconnect from the IRC server, TODO ensure this works
    def disconnect(self):
        self.sckt.shutdown(socket.SHUT_RDWR)
        self.sckt.close()
        self.sckt = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.userDone = False
        self.connected = False

    # Nickserv handling
    def nickserv(self,action,data):
        try:
            if action == "REGISTER":
                password = data[0]
                email = data[1]
                msg = f"NICKSERV REGISTER {password} {email}\r\n"
            if action == "IDENTIFY":
                password = data[0]
                msg = f"NICKSERV IDENTIFY {self.NICK} {password}\r\n"
            if action == "LOGOUT":
                msg = f"NICKSERV LOGOUT\r\n"
            if action == "DROP":
                nick = data[0]
                msg = f"NICKSERV DROP {nick}\r\n"
            self.sckt.send(bytes(msg,"UTF-8"))
        # Fail silently for any errors
        except:
            pass

    def on_connect(self):
        pass

    def on_connection_broken(self):
        pass

    def on_error(self,errorType):
        pass
    
    def on_user_join(self,who,channel,hostname):
        pass

    def on_user_part(self,who,channel,hostname):
        pass

    def on_user_quit(self,who,hostname,msg):
        pass
    
    def on_nickserv(self,msg):
        pass

    # Called on message
    def on_message(self,who,channel,msg):
        pass

    def on_whois(self,line):
        pass

    def on_names(self,channel,namesChan):
        pass
    
    def end_names(self,channel):
        pass

    def on_invalid_nick(self):
        pass
    
    def on_topic(self,chan,topic):
        pass

    def on_notice(self,chan,msg):
        pass
    
    def on_user_nick_change(self,who,newNick):
        pass

    def unknown_message(self,line):
        pass
    
    def on_server_shutdown(self):
        pass