from chalice import Chalice
from chalice import BadRequestError

app = Chalice(app_name='IoTLite')

@app.route('/')
def index():
    return {'hello': 'world'}

@app.route('/thing/{thingId}', methods=['GET'])
def one_thing(thingId):
    return {'thing': thingId }

@app.route('/thing/{thingId}/command/{command}', methods=['POST'])
def one_thing_command(thingId, command):
    payload = command_switch(command)
    if not payload:
        return { "error":"unsupported command"}
    return payload

def command_switch(argument):
    COMMANDS = {
        "on": { "power": True },
        "off": { "power": False }
    }
    try:
        return COMMANDS[argument]
    except KeyError:
        raise BadRequestError("Unknown command '%s', valid choices are: %s" % (
            argument, ', '.join(COMMANDS.keys())))

# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
