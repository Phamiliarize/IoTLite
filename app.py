import boto3
import json

from chalice import Chalice, BadRequestError, ChaliceViewError, NotFoundError

app = Chalice(app_name='IoTLite')
awsIotData = boto3.client('iot-data')
awsIot = boto3.client('iot')

@app.route('/')
def index():
    return {'hello': 'world'}

@app.route('/thing', methods=['GET'])
def list_thing():
    try:
        response = awsIot.search_index(
            queryString='thingName:*'
        )
        return response["things"]
    except (Exception, KeyError) as e:
        print(e)
        raise ChaliceViewError("A server error has occurred.")

@app.route('/thing/{name}', methods=['GET'])
def one_thing(name):
    try:
        response = awsIot.search_index(
            queryString='thingName:{}'.format(name)
        )
        return response["things"][0]
    except (IndexError, awsIot.exceptions.ResourceNotFoundException):
        raise NotFoundError("The requested thing could not be found.")
    except Exception as e:
        print(e)
        raise ChaliceViewError("A server error has occurred.")

@app.route('/thing/{name}/command/{command}', methods=['POST'])
def one_thing_command(name, command):
    payload = command_switch(command)
    try: 
        response = awsIotData.publish(
            topic='{}/command'.format(name),
            qos=1,
            payload=json.dumps(payload).encode('utf-8')
        )
    except Exception as e:
        print(e)
        raise ChaliceViewError("A server error has occurred.")

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
