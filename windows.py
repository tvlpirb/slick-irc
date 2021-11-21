#!/usr/bin/python3
# Author: Talhah Peerbhai
# Email: hello@talhah.tech

'''
This file contains the functions which create additional windows
'''

import PySimpleGUI as sg
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