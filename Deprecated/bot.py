

def checkignorelistevent(chan):
    # checkignorelist given a channel.
    for serverid in ignore["servers"]:
        if serverid == chan.server.id:
            return True

    for channelid in ignore["channels"]:
        if channelid == chan.id:
            return True
