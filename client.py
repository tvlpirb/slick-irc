#!/usr/bin/python3
# Author: Talhah Peerbhai
# Email: hello@talhah.tech

'''
This file contains the Internet Relay Chat client, it imports the irc library which
I made to abstract the IRC protocol wheras this program deals with the GUI and putting
it all together. I'm going to try to break it into more files but at the moment
this is it.
'''
from irclib import IrcCon
# PySimpleGUI is a wrapper for tkinter and some other frameworks
import PySimpleGUI as sg
import logging
import time
from windows import loginWin,errorWin,commandsWin
logging.basicConfig(filename='run.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%d-%b-%y %H:%M:%S')

sg.theme("Topanga")
#### CUSTOM EXCEPTIONS ####
class EmptyValue(Exception):
    def __init__(self):
        self.message = "User Input is required"
        super().__init__(self.message)

class InvalidCommand(Exception):
    def __init__(self):
        self.message = "User gave an invalid command"
        super().__init__(self.message)

class Client(IrcCon):
    '''
    Extend the IrcCon class which abstracts the IRC protocol so that we can 
    handle events and appropriately update the GUI
    '''
    def __init__(self,window):
        '''
        Initialise the socket and pass the GUI window to object
        '''
        IrcCon.__init__(self)
        self.window = window
    
    def on_error(self,errorType):
        if errorType == "ConnectionRefusedError":
            logging.warning(f"{errorType} Cannot connect to server")

        if errorType == "NickInUse":
            self.failedLogin = True
            logging.warning(f"{errorType}")
            #(server,host,port,nick,user,rname) = loginWin(self.HOST,self.PORT,nick,user,rname)
            #self.login(nick,user,rname)
    
    def on_message(self,who,channel,msg):
        msg = f"{current_time} | {who} > {msg}"
        if channel == self.NICK:
            channel = who
        if channel not in self.channels:
            create_tab(self.window,channel)
            openTabs.append(channel)
            self.channels.add(channel)
        self.window[f"{channel}B"].update(msg + "\n",append=True)
        markUnread(channel)

    def on_user_join(self,who,channel,hostname):
        msg = f"{current_time} | ---> {who} ({hostname}) has joined {channel}\n"
        self.window[f"{channel}B"].update(msg,text_color_for_value="green",append=True)
        markUnread(channel)
    
    def on_user_part(self,who,channel,hostname):
        msg = f"{current_time} | <--- {who} ({hostname}) has parted {channel}\n"
        self.window[f"{channel}B"].update(msg,text_color_for_value="orange",append=True)        
        markUnread(channel)

    def on_whois(self,line):
        line = line + "\n"
        self.window["infoB"].update(line,append=True)

    def unknown_message(self,line):
        # This used to "print" to infoB box which had all console output rerouted to it
        # that would apparently lead to a race condition when printing too fast? 
        # and lead to a seg fault error, hooray I guess!
        # It is important to note that pysimplegui was overriding the builtin print
        # so I'm talking about that print function. It wasn't transparent that it was
        # overriding the default one and the bug may lie therein or it's some sort of 
        # limitation. TODO Make a PR or github issue one day to fix this
        line = line + "\n"
        self.window["infoB"].update(line,append=True)


# Returns the main window layout
def mainLayout():
    # Box to display server info and other information non-specific to channels
    info = [[sg.Multiline(size=(75,15),font=('Helvetica 10'),key="infoB",reroute_stdout=False,autoscroll=True,disabled=True)]]
    menu = ['SlickIRC', ['&Exit']],['&Server'],['&Help', ['&Commands', '---', '&About']]
    layout = [[sg.Menu(menu)],
        [sg.TabGroup([[sg.Tab("info",info)]],key="chats",selected_background_color="grey")],
        [sg.Multiline(size=(70, 5), enter_submits=True, key='msgbox', do_not_clear=True),
        sg.Button('SEND', bind_return_key=True,visible=False),
        sg.Button('EXIT')
        ]]
    return layout

def create_tab(win,channel):
    if channel in tabHist:
        win[f"{channel}"].update(visible=True)
    else:
        element = [[sg.Multiline(size=(75, 15), font=('Helvetica 10'),key=f"{channel}B",autoscroll=True,disabled=True)]]
        tab = sg.Tab(f"{channel}",element,key=channel)
        win["chats"].add_tab(tab)
        tabHist.append(channel)

def delete_tab(win,channel):
    win[f"{channel}"].update(visible=False)

def markUnread(tab):
    tabgroup = mainWin["chats"].Widget
    for i in range(len(openTabs)):
        if openTabs[i] == tab:
            break
    tab = mainWin[f"{tab}"]
    title = tab.Title
    if not title.startswith("*"):
        title = "*" + title
    tabgroup.tab(i,text=title)

def markRead(tab):
    temp = tab.rstrip("*")
    tabgroup = mainWin["chats"].Widget
    for i in range(len(openTabs)):
        if openTabs[i] == temp:
            break
    title = openTabs[i]
    tabgroup.tab(i,text=title)

def processCommand(win,irc,query):
    global nick
    global loggedIn
    query = query.lstrip("/")
    try:
        if query == "":
            raise InvalidCommand
        query = query.split()
        currentTab = vals1["chats"]
        command = query[0].lower()
        if command == "join":
            channels = query[1:]
            for chan in channels:
                if chan not in irc.channels:
                    openTabs.append(chan)
                    irc.join(chan)
                    create_tab(win,chan)
        elif command == "part":
            channels = query[1:]
            for chan in channels:
                if chan in irc.channels:
                    openTabs.remove(chan)
                    delete_tab(win,chan)
                    irc.part(chan)
                else:
                    win[f"{currentTab}B"].update("Need to be in channel",append=True)
        elif command == "whois":
            if len(query) == 2:
                irc.whois(query[1])
        elif command == "unread":
            channels = query[1:]
            for chan in channels:
                if chan in irc.channels:
                    markUnread(chan)
        elif command == "nick":
            if len(query) == 2:
                nick = query[1]
                loggedIn = False
        elif command == "quit":
            msg = None
            if len(query) >= 2:
                msg = ' '.join(query[1:])
            irc.quitC(msg)
        elif command == "reconnect":
            irc.reconnect()
            for tab in openTabs[1:]:
                irc.join(tab)
        else:
            raise InvalidCommand       
    except InvalidCommand:
        logging.warning("User gave an invalid command")
        win["infoB"].update("Unknown command\n",append=True)
    finally:
        win["msgbox"].update("")

def sendMsg(win,irc,chan,msg):
    if vals1["chats"] != "info":
        irc.privmsg(f"{chan}",msg)
        msg = f"{current_time} | {irc.NICK} > " + msg + "\n"
        win[f"{chan}B"].update(msg,append=True)
    win["msgbox"].update("")

t = time.localtime()
# Initial login window
(server,port,nick,user,rname) = loginWin("127.0.0.1","6667")
# Initialize main window thereafter
mainWin = sg.Window("Slick IRC",mainLayout(),font=("Helvetica","13"),default_button_element_size=(8,2),finalize=False)
# Initialize irc client and connect
irc = Client(mainWin)
irc.connect(server,port)
loggedIn = False
failedLogin = False

# All the tabs seen so far
tabHist = ["info"]
openTabs = ["info"]
while True:
    # Event and values
    ev1, vals1 = mainWin.read(timeout=1)
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    # We haven't sucessfully logged in yet
    if not loggedIn:
        irc.login(nick,user,rname)
        loggedIn = True
    # We failed login, darn it, try again and display error
    if irc.failedLogin:
        errorWin("Nickname in use, try a different one!")
        (server,port,nick,user,rname) = loginWin(server,port,nick,user,rname)
        loggedIn = False
    if not irc.connected:
        errorWin("Cannot connect to server")
        logging.info("Asking user to enter information again")
        (server,port,nick,user,rname) = loginWin(server,port,nick,user,rname)
        irc.connect(server,port)
        irc.login(nick,user,rname)
    if ev1 == "SEND":
        query = vals1["msgbox"].rstrip()
        # Ignore bogus empty messages
        if query != "":
            # An IRC command
            if query.startswith("/"):
                processCommand(mainWin,irc,query)
            else:
                sendMsg(mainWin,irc,vals1["chats"],query)
    if vals1["chats"] != "info":
        if vals1["chats"].startswith("*"):
            markRead(vals1["chats"])
    if ev1 == "Commands":
       commandsWin() 
    # User wants to exit :(
    if ev1 == sg.WIN_CLOSED or ev1 == "EXIT" or ev1 == "Exit":
        irc.quitC()
        break
    

mainWin.close()