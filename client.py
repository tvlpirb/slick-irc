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
            errorWin("Cannot connect to server")
            logging.info("Asking user to enter information again")
            loginWin(self.HOST,self.PORT,nick,user,rname)
        if errorType == "NickInUse":
            self.failedLogin = True
            logging.warning(f"{errorType}")
            #(server,host,port,nick,user,rname) = loginWin(self.HOST,self.PORT,nick,user,rname)
            #self.login(nick,user,rname)
    
    def on_message(self,who,channel,msg):
        msg = f"{who} > {msg}"
        if channel == self.NICK:
            channel = who
        if channel not in self.channels:
            create_tab(self.window,channel)
            openTabs.append(channel)
            self.channels.add(channel)
        self.window[f"{channel}B"].update(msg + "\n",append=True)
        markUnread(channel)


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

# Window for displaying error messages
def errorWin(message):
    errorLayout = [[sg.Text(f"{message}")],
    [sg.Button("Okay",bind_return_key=True)]]
    errorWin = sg.Window("Error",errorLayout,element_justification="c",finalize=True)
    while True:
        ev3,vals3 = errorWin.read(timeout=10)
        if ev3 == sg.WIN_CLOSED or ev3 == "Okay":
            break
    errorWin.close()

# Window for entering login details for a server
# Returns a tuple containing (server,nick,user,rname)
def loginWin(serv="",port="",nick="",user="",rname=""):
    # Default to empty string if not specified
    (server,port,nick,user,rname) = (serv,port,nick,user,rname)
    # Window layout
    loginLayout = [
        [sg.Text("Server:"),sg.Multiline(size=(17,1),default_text=server,enter_submits=False, key='SERV', do_not_clear=True),
        sg.Text("Port:"),sg.Multiline(size=(6,1),default_text=port,enter_submits=False, key='PORT', do_not_clear=True)],
        [sg.Text("Alias/Nick:"),sg.Multiline(size=(25, 1), default_text=nick,enter_submits=False, key='NICK', do_not_clear=True)],
        [sg.Text("Username:"),sg.Multiline(size=(25, 1), default_text=user, enter_submits=True, key='USER', do_not_clear=True)],
        [sg.Text("Realname: (Optional)"),sg.Multiline(size=(25, 1), default_text=rname, enter_submits=True, key='RNAME', do_not_clear=True)],
        [sg.Button("CONNECT",bind_return_key=True)]
    ]
    loginWin = sg.Window("Login",loginLayout,element_justification="c",finalize=True)
    # See below link to manage switching fields when pressing enter
    # https://stackoverflow.com/questions/65923933/pysimplegui-set-and-get-the-cursor-position-in-a-multiline-widget
    b1,b2,b3,b4,b5 = loginWin["SERV"],loginWin["PORT"],loginWin["NICK"],loginWin["USER"],loginWin["RNAME"]
    # Bind return, gives an event with name KEY_Return
    b1.bind("<Return>", "_Return")
    b2.bind("<Return>", "_Return")
    b3.bind("<Return>", "_Return")
    b4.bind("<Return>","_Return")
    while True:
        ev2, vals2 = loginWin.read(timeout=10)
        try:
            if ev2 == sg.WIN_CLOSED or ev2 == "CONNECT":
                rname = loginWin["RNAME"].get()
                break
            if ev2 == "SERV_Return":
                server = loginWin["SERV"].get()
                # Upon pressing return before focus changes, new line created so we
                # get rid of that line and make sure the GUI does not display it as
                # it is ugly
                if server == "":
                    raise EmptyValue
                server = server.strip("\n")
                loginWin["SERV"].update(server)
                # Move caret to Alias field
                b2.set_focus()
            elif ev2 == "PORT_Return":
                port = loginWin["PORT"].get()
                if port == "":
                    raise EmptyValue
                port = port.strip("\n")
                loginWin["PORT"].update(port)
                # Move the caret to nick field
                b3.set_focus()
            elif ev2 == "NICK_Return":
                nick = loginWin["NICK"].get()
                if nick == "":
                    raise EmptyValue
                nick = nick.strip("\n")
                loginWin["NICK"].update(nick)
                # Move caret to username field
                b4.set_focus()
            elif ev2 == "USER_Return":
                user = loginWin["USER"].get()
                if nick == "":
                    raise EmptyValue
                user = user.strip("\n")
                loginWin["USER"].update(user)
                # Move caret to realname field
                b5.set_focus()
            #elif ev2 == "SERV_Return":
        except EmptyValue:
            logging.warning("Blank fields on login page")
            errorWin("Please fill out all the fields") 
    loginWin.close()
    return (server,int(port),nick,user,rname)

# Returns the main window layout
def mainLayout():
    # Box to display server info and other information non-specific to channels
    info = [[sg.Multiline(size=(75,15),font=('Helvetica 10'),key="infoB",reroute_stdout=False,autoscroll=True,disabled=True)]]
    layout = [[sg.Text("Chat",size=(40,1))],
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
    query = query.lstrip("/")
    try:
        if query == "":
            raise InvalidCommand
        query = query.split()
        currentTab = vals1["chats"]
        if query[0].lower() == "join":
            channels = query[1:]
            for chan in channels:
                if chan not in irc.channels:
                    openTabs.append(chan)
                    irc.join(chan)
                    create_tab(win,chan)
        elif query[0].lower() == "part":
            channels = query[1:]
            for chan in channels:
                if chan in irc.channels:
                    openTabs.remove(chan)
                    delete_tab(win,chan)
                    irc.part(chan)
                else:
                    win[f"{currentTab}B"].update("Need to be in channel",append=True)                
    except InvalidCommand:
        logging.warning("User gave an invalid command")
        win["infoB"].update("Unknown command\n",append=True)
    finally:
        win["msgbox"].update("")

def sendMsg(win,irc,chan,msg):
    if vals1["chats"] != "info":
        win[f"{chan}B"].update(f"{irc.NICK} > " + msg + "\n",append=True)
        irc.privmsg(f"{chan}",msg)
    win["msgbox"].update("")

# Initial login window
(server,port,nick,user,rname) = loginWin("127.0.0.1","6667")
# Initialize main window thereafter
mainWin = sg.Window("Slick IRC",mainLayout(),font=("Helvetica","13"),default_button_element_size=(8,2),finalize=True)
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
    ev1, vals1 = mainWin.read(timeout=10)
    # We haven't sucessfully logged in yet
    if not loggedIn:
        irc.login(nick,user,rname)
        loggedIn = True
    # We failed login, darn it, try again and display error
    if irc.failedLogin:
        errorWin("Nickname in use, try a different one!")
        (server,port,nick,user,rname) = loginWin(server,port,nick,user,rname)
        loggedIn = False
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
    # User wants to exit :(
    if ev1 == sg.WIN_CLOSED or ev1 == "EXIT":
        break
    

mainWin.close()