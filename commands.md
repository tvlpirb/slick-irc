# Connecting to an IRC server
- You need to find an IRC server which you would like to chat on, my personal favourite is [http://libera.chat/](http://libera.chat/) and [tilde.chat](https://tilde.chat)
- Enter the details of the server (host and port) and make sure to select SSL if needed
- Enter your desired alias/nick, this needs to be unique
- Enter your desired username, it doesn't need to be unique and is the username of your **connection**
- Enter a real name if you would like to specify this
- Hit connect

# Basic commands
Now that you're connected to an IRC server you'll see the info tab focused, to chat you need to join channels.

- Join channel(s), channel names typically start with # so for example #linux
```/join CHANNELNAMEHERE OTHERCHANNEL```
- Leave a channel
```/part CHANNELNAMEHERE```
- See a users details
```/whois USERNICK```
- Private message a user
```/msg USERNICK```
- Change nick/alias
```/nick NEWNICK```
- Reconnect
```/reconnect```

# Login commands
Alot of servers use NICKSERV to login, the following nickserv commands are available

- Register a nickname
```/msg NickServ REGISTER PASSWORDHERE EMAILHERE```
- Identify aka login, make sure your current nick is same as registered one
```/msg NickServ IDENTIFY PASSWORDHERE```
- Logout of nickserv
```/msg NickServ LOGOUT```
- Drop a nickname from nickserv
```/msg NickServ DROP```
