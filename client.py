#!/usr/bin/python3
# Author: Talhah Peerbhai
# Email: hello@talhah.tech
from irclib import IrcCon
# PySimpleGUI is a wrapper for tkinter and some other frameworks
import PySimpleGUI as sg
import logging

logging.basicConfig(filename='run.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%d-%b-%y %H:%M:%S')

sg.theme("Topanga")
class EmptyValue(Exception):
    def __init__(self):
        self.message = "User Input is required"
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

# Window for displaying error messages
def errorWin(message):
    errorLayout = [[sg.Text(f"{message}")],
    [sg.Button("Okay",bind_return_key=True)]]
    errorWin = sg.Window("Error",errorLayout,element_justification="c",finalize=True)
    while True:
        ev3,vals3 = errorWin.read()
        if ev3 == sg.WIN_CLOSED or ev3 == "Okay":
            break
    errorWin.close()

# Window for entering login details for a server
# Returns a tuple containing (server,nick,user,rname)
def loginWin():
    # Window layout
    loginLayout = [
        [sg.Text("Server:"),sg.Multiline(size=(25,1),enter_submits=False, key='SERV', do_not_clear=True)],
        [sg.Text("Alias/Nick:"),sg.Multiline(size=(25, 1), enter_submits=False, key='NICK', do_not_clear=True)],
        [sg.Text("Username:"),sg.Multiline(size=(25, 1), enter_submits=True, key='USER', do_not_clear=True)],
        [sg.Text("Realname: (Optional)"),sg.Multiline(size=(25, 1), enter_submits=True, key='RNAME', do_not_clear=True)],
        [sg.Button("CONNECT",bind_return_key=True)]
    ]
    loginWin = sg.Window("Login",loginLayout,element_justification="c",finalize=True)
    # See below link to manage switching fields when pressing enter
    # https://stackoverflow.com/questions/65923933/pysimplegui-set-and-get-the-cursor-position-in-a-multiline-widget
    b1,b2,b3,b4 = loginWin["SERV"],loginWin["NICK"],loginWin["USER"],loginWin["RNAME"]
    # Bind return, gives an event with name KEY_Return
    b1.bind("<Return>", "_Return")
    b2.bind("<Return>", "_Return")
    b3.bind("<Return>", "_Return")
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
            elif ev2 == "NICK_Return":
                nick = loginWin["NICK"].get()
                if nick == "":
                    raise EmptyValue
                nick = nick.strip("\n")
                loginWin["NICK"].update(nick)
                # Move caret to username field
                b3.set_focus()
            elif ev2 == "USER_Return":
                user = loginWin["USER"].get()
                if nick == "":
                    raise EmptyValue
                user = user.strip("\n")
                loginWin["USER"].update(user)
                # Move caret to realname field
                b4.set_focus()
        except EmptyValue:
            logging.warning("Blank fields on login page")
            errorWin("Please fill out all the fields")
        
    loginWin.close()
    return (server,nick,user,rname)

def mainLayout():
    info = [[sg.Multiline(size=(75,15),font=('Helvetica 10'),key="info",reroute_stdout=True,autoscroll=True)]]
    layout = [[sg.Text("Chat",size=(40,1))],
        [sg.TabGroup([[sg.Tab("info",info)]],key="chats",selected_background_color="grey")],
        [sg.Multiline(size=(70, 5), enter_submits=True, key='msgbox', do_not_clear=True),
        sg.Button('SEND', bind_return_key=True,visible=False),
        sg.Button('EXIT')
        ]]
    return layout

(server,nick,user,rname) = loginWin()
