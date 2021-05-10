import os
import boto3
import json
import uuid

from chalice import Chalice, BadRequestError, ChaliceViewError, NotFoundError, Response
from chalicelib import serializers, commands


app = Chalice(app_name='IoTLite')

DEL_SQS_URL = os.getenv("DELETE_SQS_URL", default="https://fake.ap-north-east1.aws.com/queue/0123456789/IoTLite-delete-queue") # ユニットテスト用、default
DEL_SQS_NAME = os.getenv("DELETE_SQS_NAME", default="IoTLite-delete-queue")

iot_data = boto3.client('iot-data')
iot = boto3.client('iot')
sqs = boto3.client('sqs')


# GET: ライト一覧を取得 POST: 新しいライトを登録 (入力はない)
@app.route('/light', methods=['GET', 'POST'])
def list_light():
    request = app.current_request
    if request.method == 'GET':
        # PENDING_DELETEがソフト削除担っているので、表示しない
        search_kwargs = dict(queryString='thingName:* AND -attributes.PENDING_DELETE:true')
        if request.query_params and request.query_params.get('nextToken'):
            search_kwargs['nextToken'] = request.query_params.get('nextToken')
        if request.query_params and request.query_params.get('limit'):
            search_kwargs['maxResults'] = int(request.query_params.get('limit'))
        try:
            # handle next token/pagination
            response = iot.search_index(**search_kwargs)
            return {
                'lights': [serializers.light(thing) for thing in response['things']],
                'nextToken': response.get('nextToken', None)
            }
        except iot.exceptions.InvalidRequestException as e:
            raise BadRequestError(e)
        except (Exception, KeyError) as e:
            app.log.error(e)
            raise ChaliceViewError('A server error has occurred.')
    if request.method == 'POST':
        lightId = str(uuid.uuid4())
        try:
            cert = iot.create_keys_and_certificate(
                setAsActive=True
            )

            attach_policy = iot.attach_policy(
                policyName='IoTLiteLightPolicy',
                target=cert['certificateArn']
            )

            thing = iot.create_thing(
                thingName=lightId,
            )

            attach_cert = iot.attach_thing_principal(
                thingName=lightId,
                principal=cert['certificateArn']
            )

            return Response(body=serializers.new_device(thing, cert),
                status_code=201,
                headers={'Content-Type': 'application/json'})
        except (Exception, KeyError) as e:
            app.log.error(e)
            raise ChaliceViewError(e)


# GET: １台のライトを取得 DELETE: １台のライトを削除
@app.route('/light/{id}', methods=['GET', 'DELETE'])
def one_light(id):
    request = app.current_request
    try:
        if request.method == 'GET':
            response = iot.search_index(
                queryString='thingName:{} AND -attributes.PENDING_DELETE:true'.format(id)
            )
            return serializers.light(response['things'][0])
        if request.method == 'DELETE':
            certARN = iot.list_thing_principals(
                thingName=id
            )['principals'][0]

            # 非同期なので、今すぐ消すことができないです。
            detach_cert = iot.detach_thing_principal(
                thingName=id,
                principal=certARN
            )

            response = iot.update_thing(
                thingName=id,
                attributePayload={
                    'attributes': {
                        'PENDING_DELETE': 'true'
                    },
                    'merge': True
                }
            )

            inactivate_cert = iot.update_certificate(
                certificateId=certARN.split("/")[1],
                newStatus='INACTIVE'
            )

            # ハード削除を非同期にするため、SQSにMSGを送信
            SQS = sqs.send_message(
                QueueUrl=DEL_SQS_URL,
                MessageBody=json.dumps({"certARN":certARN,"thingName":id})
            )
        return Response(body=None,
                status_code=204,
                headers={'Content-Type': 'application/json'})

    except (IndexError, iot.exceptions.ResourceNotFoundException):
        raise NotFoundError('The requested light could not be found.')
    except Exception as e:
        app.log.error(e)
        raise ChaliceViewError('A server error has occurred.')


# ライトを１台にコマンドを送信
# chancelib/commandsで新しいコマンドを追加
@app.route('/light/{id}/command/{command}', methods=['POST'])
def one_light_command(id, command):
    try:
        payload = commands.switch(command)
        response = iot_data.publish(
            topic='{}/command'.format(id),
            qos=1,
            payload=json.dumps(payload).encode('utf-8')
        )
    except KeyError:
        raise BadRequestError('Unknown command: {}"'.format(command))
    except Exception as e:
        app.log.error(e)
        raise ChaliceViewError('A server error has occurred.')

    return serializers.command(id, payload)


# ChaliceでSQSのラムダ管理する
@app.on_sqs_message(queue=DEL_SQS_NAME, batch_size=1)
def handle_sqs_message(event):
    for record in event:
        payload = json.loads(record.body)
        try:
            
            delete_cert = iot.delete_certificate(
                certificateId=payload["certARN"].split("/")[1],
                forceDelete=True
            )
        
            delete_thing = iot.delete_thing(
                thingName=payload["thingName"]
            )
            
            response = sqs.delete_message(
                QueueUrl=DEL_SQS_URL,
                ReceiptHandle=getattr(record, 'receiptHandle', record.receipt_handle)
            )
            return response
        except (Exception, iot.exceptions.ResourceNotFoundException) as e:
            app.log.error(e)