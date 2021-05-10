def switch(argument):
    COMMANDS = {
        'on': {'power': True},
        'off': {'power': False}
    }
    return COMMANDS[argument]