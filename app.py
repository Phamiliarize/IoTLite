import boto3
import json
import uuid

from chalice import Chalice, BadRequestError, ChaliceViewError, NotFoundError
from chalicelib import serializers, commands

app = Chalice(app_name='IoTLite')
awsIotData = boto3.client('iot-data')
awsIot = boto3.client('iot')


@app.route('/')
def index():
    return {'hello': 'world'}


# GET: ライト一覧を取得 POST: 新しいライトを登録
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
            print(response)
            return {
                'lights': [serializers.light(thing) for thing in response['things']],
                'nextToken': response.get('nextToken', None)
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

            thing = awsIot.create_thing(
                thingName=lightId,
            )

            attach_cert = awsIot.attach_thing_principal(
                thingName=lightId,
                principal=cert['certificateArn']
            )

            return serializers.new_device(thing, cert)
        except (Exception, KeyError) as e:
            print(e)
            raise ChaliceViewError(e)


# GET: １台のライトを取得 DELETE: １台のライトを削除
@app.route('/light/{id}', methods=['GET', 'DELETE'])
def one_light(id):
    request = app.current_request
        try:
            if request.method == 'GET':
                response = awsIot.search_index(
                    queryString='thingName:{}'.format(id)
                )
                return serializers.light(response['things'][0])
            if request.method == 'DELETE':
                certARN = client.list_thing_principals(
                    thingName={id}
                )['principals'][0]

                # 非同期なので、今すぐ消すことができないです。
                client.detach_thing_principal(
                    thingName=id,
                    principal=certARN
                )

                # set PENDING_DELETE attribute, add to delete sqs
                
                # SQSで
                # inactivate_cert = awsIot.update_certificate(
                #     certificateId=certARN,
                #     newStatus='INACTIVE'
                # )

                # delete_cert = client.delete_certificate(
                #     certificateId=certARN,
                #     forceDelete=True
                # )

                # delete_thing = awsIot.delete_thing(
                #     thingName=id
                # )
            return Response(body=None,
                    status_code=204,
                    headers={'Content-Type': 'application/json'})

        except (IndexError, awsIot.exceptions.ResourceNotFoundException):
            raise NotFoundError('The requested light could not be found.')
        except Exception as e:
            print(e)
            raise ChaliceViewError('A server error has occurred.')


# ライトを１台にコマンドを送信
# chancelib/commandsで新しいコマンドを追加
@app.route('/light/{id}/command/{command}', methods=['POST'])
def one_light_command(id, command):
    payload = commands.switch(command)
    try:
        response = awsIotData.publish(
            topic='{}/command'.format(id),
            qos=1,
            payload=json.dumps(payload).encode('utf-8')
        )
    except Exception as e:
        print(e)
        raise ChaliceViewError('A server error has occurred.')

    return serializers.command(id, payload)
