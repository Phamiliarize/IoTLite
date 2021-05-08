def switch(argument):
    COMMANDS = {
        'on': {'power': True},
        'off': {'power': False}
    }
    try:
        return COMMANDS[argument]
    except KeyError:
        raise BadRequestError('Unknown command "%s", valid choices are: %s' % (
            argument, ', '.join(COMMANDS.keys())))