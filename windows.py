#!/usr/bin/python3
# Author: Talhah Peerbhai
# Email: hello@talhah.tech

'''
This file contains the functions which create additional windows
'''

import PySimpleGUI as sg
import webbrowser

class EmptyValue(Exception):
    def __init__(self):
        self.message = "User Input is required"
        super().__init__(self.message)

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
    ssl = False
    # Window layout
    loginLayout = [
        [sg.Text("Server:"),sg.Multiline(size=(17,1),default_text=server,enter_submits=False, key='SERV', do_not_clear=True),
        sg.Text("Port:"),sg.Multiline(size=(6,1),default_text=port,enter_submits=False, key='PORT', do_not_clear=True),sg.Checkbox("SSL",default=True,key="SSL")],
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
                ssl = vals2["SSL"]
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
            errorWin("Please fill out all the fields") 
    loginWin.close()
    return (server,int(port),nick,user,rname,ssl)

def commandsWin():
    font = ("Courier New",16,"underline")
    comWinLayout = [[sg.Text("Online guide sheet, click me",enable_events=True,font=font,key="link")],
        [sg.Button("Okay",bind_return_key=True)]]
    comWin = sg.Window("Command",comWinLayout,element_justification="c",finalize=True)
    while True:
        ev4, vals4 = comWin.read(timeout=10)
        if ev4 == sg.WIN_CLOSED or ev4 == "Okay":
            break
        elif ev4 == "link":
            webbrowser.open("https://github.com/tvlpirb/slick-irc/blob/master/commands.md")
            comWin["link"].update("Opening in browser")
    comWin.close()

def aboutWin():
    aboutWinLayout = [[sg.Text("Slick IRC is a simple and easy to use Internet Relay Chat client.\n\nIt was developed for my term project, 112@cmuq and \nmost likely will not see any further development.\n\nDeveloped by Talhah Peerbhai (hello@talhah.tech)\n\nVersion: 1.0\n\nLast update: 2021-11-24\n")],
    [sg.Button("Okay",bind_return_key=True)]]
    aboutWin = sg.Window("About",aboutWinLayout,element_justification="c",finalize=True)
    while True:
        ev5, vals5 = aboutWin.read(timeout=10)
        if ev5 == sg.WIN_CLOSED or ev5 == "Okay":
            break
    aboutWin.close()

def filterWin(flist):
    filterWinLayout = [[sg.Text("Filter list")],
    [sg.Listbox(values=flist,key="box",size=(10,10),expand_x=True,expand_y=True)],
    [sg.Multiline("",size=(10,1),key="item",enter_submits=True,do_not_clear=True)],
    [sg.Button("Add",bind_return_key=True),sg.Button("Exit")]]
    filterWin = sg.Window("About",filterWinLayout,element_justification="c",finalize=True,resizable=True)
    while True:
        ev6, vals6 = filterWin.read(timeout=10)
        if ev6 == "Add":
            item = filterWin["item"].get()
            item.rstrip()
            item.lstrip()
            item.strip("\n")
            if item != "":
                if item not in flist:
                    item = item.lower()
                    flist.append(item)
                    filterWin["box"].update(values=flist)
                filterWin["item"].update("")     
        if ev6 == sg.WIN_CLOSED or ev6 == "Exit":
            break
    filterWin.close()
    return flist