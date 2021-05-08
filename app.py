import boto3
import json
import uuid

from chalice import Chalice, BadRequestError, ChaliceViewError, NotFoundError

app = Chalice(app_name='IoTLite')
awsIotData = boto3.client('iot-data')
awsIot = boto3.client('iot')


@app.route('/')
def index():
    return {'hello': 'world'}


@app.route('/light', methods=['GET', 'POST'])
def list_light():
    request = app.current_request
    if request.method == 'GET':
        search_kwargs = dict(queryString='thingName:*')
        if request.query_params and request.query_params.get('nextToken'):
            search_kwargs['nextToken'] = request.query_params.get('nextToken')
        try:
            # handle next token/pagination
            response = awsIot.search_index(**search_kwargs)
            return {
                'lights': [light_serializer(thing) for thing in response['things']],
                'nextToken': getattr(response, 'nextToken', None)
            }
        except awsIot.exceptions.InvalidRequestException as e:
            raise BadRequestError(e)
        except (Exception, KeyError) as e:
            print(e)
            raise ChaliceViewError('A server error has occurred.')
    if request.method == 'POST':
        lightId = str(uuid.uuid4())
        try:
            cert = awsIot.create_keys_and_certificate(
                setAsActive=True
            )

            attach_policy = awsIot.attach_policy(
                policyName='lightPolicy',
                target=cert['certificateArn']
            )

            response = awsIot.create_thing(
                thingName=lightId,
            )

            attach_cert = awsIot.attach_thing_principal(
                thingName=lightId,
                principal=cert['certificateArn']
            )

            return {
                'id': response['thingName'],
                'cert': cert['certificatePem'],
                'publicKey': cert['keyPair']['PublicKey'],
                'privateKey': cert['keyPair']['PrivateKey']
            }
        except (Exception, KeyError) as e:
            print(e)
            raise ChaliceViewError(e)


@app.route('/light/{name}', methods=['GET'])
def one_light(name):
    try:
        response = awsIot.search_index(
            queryString='thingName:{}'.format(name)
        )
        return light_serializer(response['things'][0])
    except (IndexError, awsIot.exceptions.ResourceNotFoundException):
        raise NotFoundError('The requested light could not be found.')
    except Exception as e:
        print(e)
        raise ChaliceViewError('A server error has occurred.')


@app.route('/light/{name}/command/{command}', methods=['POST'])
def one_light_command(name, command):
    payload = command_switch(command)
    try:
        response = awsIotData.publish(
            topic='{}/command'.format(name),
            qos=1,
            payload=json.dumps(payload).encode('utf-8')
        )
    except Exception as e:
        print(e)
        raise ChaliceViewError('A server error has occurred.')

    return payload


def command_switch(argument):
    COMMANDS = {
        'on': {'power': True},
        'off': {'power': False}
    }
    try:
        return COMMANDS[argument]
    except KeyError:
        raise BadRequestError('Unknown command "%s", valid choices are: %s' % (
            argument, ', '.join(COMMANDS.keys())))

def light_serializer(obj):
    return {
        "id": obj["thingName"],
        "connectivity": obj["connectivity"]
    }