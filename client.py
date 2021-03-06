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
import time
from colorhash import ColorHash as chash
from windows import loginWin,errorWin,commandsWin,aboutWin,filterWin
from sys import platform
import os
import datetime

if platform == "darwin" or platform == "win32":
    print("\033[93mUnsupported Operating System, this program only works on Linux\033[0m")
    raise OSError

sg.theme("SystemDefault")
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
            pass

        if errorType == "NickInUse":
            self.failedLogin = True
            pass
    
    def on_message(self,who,channel,msg):
        #msg = f"{current_time} | {who} > {msg}"
        check = msg.lower()
        check = set(check.split())
        # Filter out messages
        for item in fList:
            if item in check:
                return
        if channel == self.NICK:
            channel = who
        if channel not in self.channels:
            create_tab(self.window,channel)
            openTabs.append(channel)
            self.channels.add(channel)
        ms = f"{current_time} | "
        self.window[f"{channel}B"].update(ms,append=True)
        ms = f"{who} "
        color = chash(f"{who}").hex
        self.window[f"{channel}B"].update(ms,text_color_for_value=color,append=True)
        msg = f"> {msg}"
        self.window[f"{channel}B"].update(msg + "\n",append=True)
        markUnread(channel)

    def on_user_join(self,who,channel,hostname):
        msg = f"{current_time} | ---> {who} ({hostname}) has joined {channel}\n"
        self.window[f"{channel}B"].update(msg,text_color_for_value="green",append=True)
        markUnread(channel)
        # Add user to the names list
        namesList = names[channel]
        namesList.append(who)
        namesList.sort()
        names[channel] = namesList
        self.window[f"{channel}L"].update(values=names[channel])
    
    def on_user_part(self,who,channel,hostname):
        msg = f"{current_time} | <--- {who} ({hostname}) has parted {channel}\n"
        self.window[f"{channel}B"].update(msg,text_color_for_value="orange",append=True)        
        markUnread(channel)
        # Remove the user from the names list
        namesList = names[channel]
        if who in namesList:
            namesList.remove(who)
        elif f"@{who}" in namesList:
            namesList.remove(f"@{who}")
        elif f"~{who}" in namesList:
            namesList.remove(f"~{who}")
        elif f"+{who}" in namesList:
            namesList.remove(f"+{who}")
        names[channel] = namesList
        self.window[f"{channel}L"].update(values=names[channel])
    
    def on_user_nick_change(self,who,newNick):
        msg = f"{current_time} | {who} is now known as {newNick}\n"
        for chan in names:
            if who in names[chan]:
                self.window[f"{chan}B"].update(msg,text_color_for_value="blue",append=True)
                # Update the users name in the name list
                namesList = names[chan]
                # handle nick changes when +,~ @ in front of name, we need to preserve
                # the leading inidicator
                if who in namesList:
                    namesList.remove(who)
                elif f"@{who}" in namesList:
                    namesList.remove(f"@{who}")
                    newNick = "@" + newNick
                elif f"~{who}" in namesList:
                    namesList.remove(f"~{who}")
                    newNick = "~" + newNick
                elif f"+{who}" in namesList:
                    namesList.remove(f"+{who}")
                    newNick = "+" + newNick
                namesList.append(newNick)
                namesList.sort()
                names[chan] = namesList
                markUnread(chan)
                self.window[f"{chan}L"].update(values=names[chan])
    
    def on_user_quit(self,who,hostname,msg):
        msg = f"{current_time} | {who} ({hostname}) quit: {msg}\n"
        for chan in names:
            inChan = False
            # Update the users name in the name list
            namesList = names[chan]
            # A name may have a leading +,~ @ so we need to appropriately remove
            # user from the names list
            if who in namesList:
                namesList.remove(who)
                inChan = True
            elif f"@{who}" in namesList:
                namesList.remove(f"@{who}")
                inChan = True
            elif f"~{who}" in namesList:
                namesList.remove(f"~{who}")
                inChan = True
            elif f"+{who}" in namesList:
                namesList.remove(f"+{who}")
                inChan = True
            if inChan:
                self.window[f"{chan}B"].update(msg,text_color_for_value="red",append=True)
                names[chan] = namesList
                markUnread(chan)
                self.window[f"{chan}L"].update(values=names[chan])

    def on_topic(self,chan,topic):
        self.window[f"{chan}T"].update(topic)

    def on_whois(self,line):
        line = line[3:]
        line = ' '.join(line)
        msg = f"{current_time} | {line}\n"
        self.window["infoB"].update(msg,append=True)
        markUnread("info")

    def unknown_message(self,line):
        # This used to "print" to infoB box which had all console output rerouted to it
        # that would apparently lead to a race condition when printing too fast? 
        # and lead to a seg fault error, fixed now so hooray I guess!
        # It is important to note that pysimplegui was overriding the builtin print
        # so I'm talking about that "print" function. It wasn't transparent that it was
        # overriding the default one and the bug may lie therein or it's some sort of 
        # limitation. TODO Make a PR or github issue one day to fix this
        line = f"{current_time} | " + line + "\n"
        self.window["infoB"].update(line,append=True)
        markUnread("info")
    
    def on_nickserv(self,msg):
        msg = f"{current_time} | " + "NickServ " + msg + "\n"
        self.window["infoB"].update(msg,text_color_for_value="dark red",font_for_value="Helvetica 10 bold",append=True)
        markUnread("info")
        
    def on_names(self,channel,namesChan):
        namesChan[0] = namesChan[0].lstrip(":")
        if channel not in names:
            names[channel] = []
        names[channel] = names[channel] + namesChan

    def end_names(self,channel):
        nameslist = names[channel]
        nameslist.sort()
        names[channel] = nameslist
        time.sleep(1)
        self.window[f"{channel}L"].update(values=names[channel])
    
    def on_list(self,channel,members):
        msg = f"{current_time} | Chan: {channel} Members: {members}\n"
        self.window["infoB"].update(msg,append=True,text_color_for_value="dark green",font_for_value=("Helvetica",10,"bold"))
    def on_notice(self,chan,msg):
        if chan not in openTabs:
            create_tab(self.window,chan)
            self.channels.add(chan)
            openTabs.append(chan)
        msg = f"{current_time} | " + "Notice " + msg + "\n"
        font = ("Helvetica",10,"bold")
        if msg == "Server is shutting down":
            self.disconnect()
        self.window[f"{chan}B"].update(msg,text_color_for_value="dark red",font_for_value=font,append=True)
        markUnread(chan)

# Returns the main window layout
def mainLayout():
    # Box to display server info and other information non-specific to channels
    info = [[sg.Multiline(size=(93,19),font=('Helvetica 10'),key="infoB",reroute_stdout=False,autoscroll=True,disabled=True)]]
    menu = ['SlickIRC', ['&Exit']],['&Server',['Server settings']],["&Filters",['Filter settings']],['&Help', ['&Commands', '---', '&About'],]
    layout = [[sg.Menu(menu)],
        [sg.TabGroup([[sg.Tab("info",info)]],key="chats",selected_background_color="grey")],
        [sg.Multiline(size=(59, 2), enter_submits=True, key='msgbox', do_not_clear=True),
        sg.Button('SEND', bind_return_key=True,visible=True),
        sg.Button('EXIT',visible=False)
        ]]
    return layout

# Creates a new tab, we keep a record of tabs created, so if a this tab exists 
# in hist then we just unhide it 
def create_tab(win,channel):
    if channel in tabHist:
        win[f"{channel}"].update(visible=True)
    else:
        leftCol = [[sg.Multiline("No channel topic",size=(75, 3), font=('Helvetica 10'),key=f"{channel}T",autoscroll=False,disabled=True)],
        [sg.Multiline(size=(75, 15), font=('Helvetica 10'),key=f"{channel}B",autoscroll=True,disabled=True)]]
        rightCol = [[sg.Listbox(values=[""],key=f"{channel}L",size=(10,13))]]
        element = [[sg.Column(leftCol),sg.Column(rightCol)]]
        tab = sg.Tab(f"{channel}",element,key=channel)
        win["chats"].add_tab(tab)
        load_tab(channel)
        tabHist.append(channel)

# Deletes a tab, we don't truly delete it but just hide it. I can delete a tab
# but unable to delete the contents related to it and we have issues if we need to
# recreate this tab. Hiding it isn't too bad of a tradeoff and history is preserved
def delete_tab(win,channel):
    win[f"{channel}"].update(visible=False)

def save_tab(tab):
    if not os.path.exists("chatlog"):
        os.mkdir("chatlog")
    if not os.path.exists(f"chatlog/{irc.HOST}"):
        os.mkdir(f"chatlog/{irc.HOST}")
    f = open(f"chatlog/{irc.HOST}/{tab}.txt","w+")
    tabLog = mainWin[f"{tab}B"].get()
    tabLog = tabLog.splitlines(True)
    try:
        index = len(tabLog)-tabLog[::-1].index("======= End of backlog =======\n")-1
    except ValueError:
        index = 0
    today = datetime.date.today()
    date = today.strftime("%B %d, %Y")
    tabLog.insert(index,f"======= {date} =======\n")
    tabLog = ' '.join(tabLog)
    f.write(tabLog)
    f.close()

def load_tab(tab):
    if os.path.exists(f"chatlog/{irc.HOST}/{tab}.txt"):
        f = open(f"chatlog/{irc.HOST}/{tab}.txt","r")
        hist = f.read()
        hist = hist + "\n" + "======= End of backlog =======\n"
        mainWin[f"{tab}B"].update(hist,append=True)
        f.close()

# Add an asterisk infront of a tabs name to indicate there is an unread message
def markUnread(tab):
    tabgroup = mainWin["chats"].Widget
    # Get the index of the tab, we add to openTabs elsewhere so we can get index
    # over here
    for i in range(len(openTabs)):
        if openTabs[i] == tab:
            break
    # Get the tab object
    tab = mainWin[f"{tab}"]
    title = tab.Title
    # Only if it isn't already unread append an asterisk
    if not title.startswith("*"):
        title = "*" + title
    tabgroup.tab(i,text=title)

# Mark a tab as read by removing the asterisk at the start of its name
def markRead(tab):
    temp = tab.lstrip("*")
    tabgroup = mainWin["chats"].Widget
    for i in range(len(openTabs)):
        if openTabs[i] == temp:
            break
    title = openTabs[i]
    tabgroup.tab(i,text=title)

# Process IRC commands such as /join etc.
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
                    names[chan] = []
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
            quit()
        elif command == "reconnect":
            irc.reconnect()
            for tab in openTabs[1:]:
                irc.join(tab)
        elif command == "query" or command == "msg":
            nick = query[1]
            if nick == "NickServ":
                # Make sure that there's enough params
                if len(query) > 2:
                    irc.nickserv(query[2],query[3:])
                else:
                    raise InvalidCommand
            else:
                openTabs.append(nick)
                irc.join(nick)
                create_tab(win,nick)
                if len(query) > 2:
                    msg = ' '.join(query[2:])
                    sendMsg(win,irc,nick,msg)
        elif command == "save":
            channels = query[1:]
            if len(channels) >= 1:
                for tab in channels:
                    if tab in tabHist:
                        save_tab(tab)
            else:
                for tab in tabHist:
                    save_tab(tab)
            msg = "Sucessfully saved chat(s) in folder chatlog\n"
            font = ("Helvetica",10,"bold")
            mainWin[f"{currentTab}B"].update(msg,text_color_for_value="dark red",font_for_value=font,append=True) 
        elif command == "list":
            irc.listChan()
        else:
            raise InvalidCommand       
    except InvalidCommand:
        win["infoB"].update("Unknown command\n",append=True)
    finally:
        win["msgbox"].update("")

# Send a message to a channel or private message
# We break the string down to color the users own nick for better readability
def sendMsg(win,irc,chan,msg):
    # We don't send messages in the info channel
    if chan != "info":
        irc.privmsg(f"{chan}",msg)
        ms = f"{current_time} | "
        win[f"{chan}B"].update(ms,append=True)
        ms = f"{irc.NICK} "
        win[f"{chan}B"].update(ms,text_color_for_value="purple",append=True)
        msg = "> " + msg + "\n"
        win[f"{chan}B"].update(msg,append=True)
    # Clear message box
    win["msgbox"].update("")

t = time.localtime()
# Initial login window
(server,port,nick,user,rname,ssl) = loginWin("irc.tilde.chat","6697")
# Initialize main window thereafter
mainWin = sg.Window("Slick IRC",mainLayout(),font=("Helvetica","13"),default_button_element_size=(8,2),finalize=True)
# Initialize irc client and connect
irc = Client(mainWin)
irc.connect(server,port,ssl)
loggedIn = False
failedLogin = False
fList = []

# All the tabs seen so far
tabHist = ["info"]
openTabs = ["info"]
names = dict()
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
        (server,port,nick,user,rname,ssl) = loginWin(server,port,nick,user,rname)
        loggedIn = False
    if not irc.connected:
        errorWin("Cannot connect to server")
        (server,port,nick,user,rname,ssl) = loginWin(server,port,nick,user,rname)
        irc.connect(server,port,ssl)
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
    # Mark a channel as read:
    if vals1["chats"].startswith("*"):
        markRead(vals1["chats"])
    if ev1 == "Server settings":
        (oldServ,oldPort) = (server,port)
        (server,port,nick,user,rname,ssl) = loginWin(server,port,nick,user,rname)
        if oldServ != server or oldPort != port:
            irc.disconnect()
            irc.connect(server,port,ssl)
        irc.login(nick,user,rname)
    if ev1 == "Commands":
        commandsWin() 
    if ev1 == "Filter settings":
        fList = filterWin(fList)
    if ev1 == "About":
        aboutWin()
    # User wants to exit :(
    if ev1 == sg.WIN_CLOSED or ev1 == "EXIT" or ev1 == "Exit":
        irc.quitC()
        break
    

mainWin.close()