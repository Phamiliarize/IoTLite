import json
import uuid
import pytest

from chalice.test import Client
from botocore.stub import Stubber, ANY

import app


# ライト一覧を取得
def test_list_light_get():
    lightId = str(uuid.uuid4())
    thingId = str(uuid.uuid4())
    iot_stub = Stubber(app.iot)

    iot_stub.add_response(
        'search_index',
        expected_params={
            'queryString': 'thingName:* AND -attributes.PENDING_DELETE:true',
        },
        service_response={
            'things': [
                {
                    'thingName': lightId,
                    'thingId': thingId,
                    'thingTypeName': 'string',
                    'attributes': {
                        'string': 'string'
                    },
                    'shadow': 'string',
                    'connectivity': {
                        'connected': True,
                        'timestamp': 123
                    }
                },
            ]
        }
    )

    with iot_stub:
        with Client(app.app) as client:
            response = client.http.get('/light')
            print(response.json_body)
            assert response.json_body == {
                'lights': [{'id': lightId, 'connectivity': {'connected': True, 'timestamp': 123}}],
                'nextToken': None
            }


# ライト一覧をリミットで取得　（nextTokenも返すことを確認）
def test_list_light_get_limit_next():
    lightId = str(uuid.uuid4())
    thingId = str(uuid.uuid4())
    iot_stub = Stubber(app.iot)

    iot_stub.add_response(
        'search_index',
        expected_params={
            'queryString': 'thingName:* AND -attributes.PENDING_DELETE:true',
            'maxResults': 1
        },
        service_response={
            'things': [
                {
                    'thingName': lightId,
                    'thingId': thingId,
                    'thingTypeName': 'string',
                    'attributes': {
                        'string': 'string'
                    },
                    'shadow': 'string',
                    'connectivity': {
                        'connected': True,
                        'timestamp': 123
                    }
                },
                {
                    'thingName': thingId,
                    'thingId': lightId,
                    'thingTypeName': 'string',
                    'attributes': {
                        'string': 'string'
                    },
                    'shadow': 'string',
                    'connectivity': {
                        'connected': True,
                        'timestamp': 123
                    }
                }
            ],
            'nextToken': "AQIPPlK0ud9zpBYJm5SANTsFxcAbTUgvN9Sw5Q5/2dXsvs1nN5mmkuWKc7vNQ0LhzDt5z3YkkUEUKvcJvPK7CDFYFahqt+WDimT8X/sNu/QoxE1pYw+86nIREhJsSezafWODy1nt/MtpiYlfCrtykmafZU12gC8pbdFWtTEWN5ElPnPWs+9bp1e/GMap02tjFHVXWt5qGcXJNg=="
        }
    )

    with iot_stub:
        with Client(app.app) as client:
            response = client.http.get('/light?limit=1')
            assert response.json_body["nextToken"] != None


# 新しいライトを登録
def test_list_light_post():
    lightId = str(uuid.uuid4())
    iot_stub = Stubber(app.iot)

    iot_stub.add_response(
        'create_keys_and_certificate',
        expected_params={
            'setAsActive': True
        },
        service_response={
            'certificateArn': 'e9Bo7GlWCDtZefEZBGGgnI0szWYIhU1k9BUY81LqB04pmM0mydu2WmWIvqg6PfrV',
            'certificateId': 'e9Bo7GlWCDtZefEZBGGgnI0szWYIhU1k9BUY81LqB04pmM0mydu2WmWIvqg6PfrV',
            'certificatePem': 'string',
            'keyPair': {
                'PublicKey': 'string',
                'PrivateKey': 'string'
            }
        }
    )

    iot_stub.add_response(
        'attach_policy',
        expected_params={
            'policyName': 'lightPolicy',
            'target': 'e9Bo7GlWCDtZefEZBGGgnI0szWYIhU1k9BUY81LqB04pmM0mydu2WmWIvqg6PfrV'
        },
        service_response={}
    )

    iot_stub.add_response(
        'create_thing',
        expected_params={
            'thingName': ANY
        },
        service_response={
            'thingName': lightId,
            'thingArn': 'string',
            'thingId': 'string'
        }
    )

    iot_stub.add_response(
        'attach_thing_principal',
        expected_params={
            'thingName': ANY,
            'principal': 'e9Bo7GlWCDtZefEZBGGgnI0szWYIhU1k9BUY81LqB04pmM0mydu2WmWIvqg6PfrV'
        },
        service_response={}
    )

    with iot_stub:
        with Client(app.app) as client:
            response = client.http.post('/light')
            assert response.json_body == {
                "id": lightId,
                "cert": "string",
                "publicKey": "string" ,
                "privateKey": "string" ,
                "topics": [
                    "{}/data".format(lightId),
                    "{}/command".format(lightId)
                ]
            }


# 一台のライトを取得
def test_one_light_get():
    lightId = str(uuid.uuid4())
    thingId = str(uuid.uuid4())
    iot_stub = Stubber(app.iot)

    iot_stub.add_response(
        'search_index',
        expected_params={
            'queryString': 'thingName:{} AND -attributes.PENDING_DELETE:true'.format(lightId),
        },
        service_response={
            'things': [
                {
                    'thingName': lightId,
                    'thingId': thingId,
                    'thingTypeName': 'string',
                    'attributes': {
                        'string': 'string'
                    },
                    'shadow': 'string',
                    'connectivity': {
                        'connected': True,
                        'timestamp': 123
                    }
                },
            ]
        }
    )

    with iot_stub:
        with Client(app.app) as client:
            response = client.http.get('/light/{}'.format(lightId))
            assert response.json_body == {
                'id': lightId,
                'connectivity': {
                    'connected': True,
                    'timestamp': 123
                }
            }


# 一台のライトを取得 (ない場合)
def test_one_light_get():
    lightId = str(uuid.uuid4())
    thingId = str(uuid.uuid4())
    iot_stub = Stubber(app.iot)

    iot_stub.add_response(
        'search_index',
        expected_params={
            'queryString': 'thingName:{} AND -attributes.PENDING_DELETE:true'.format(lightId),
        },
        service_response={
            'things': []
        }
    )

    with iot_stub:
        with Client(app.app) as client:
            response = client.http.get('/light/{}'.format(lightId))
            assert response.status_code == 404


# 一台のライトを削除 (ない場合)
def test_one_light_delete():
    lightId = str(uuid.uuid4())
    thingId = str(uuid.uuid4())
    iot_stub = Stubber(app.iot)

    iot_stub.add_response(
        'list_thing_principals',
        expected_params={
            'thingName': lightId,
        },
        service_response={
            'principals': [
                'e9Bo7GlWCDtZefEZBGGgnI0szWYIhU1k9BUY81LqB04pmM0mydu2WmWIvqg6PfrV',
            ],
            'nextToken': 'string'
        }
    )

    # here
    iot_stub.add_response(
        'detach_thing_principal',
        expected_params={
            'thingName': lightId,
        },
        service_response={
            'principals': [
                'e9Bo7GlWCDtZefEZBGGgnI0szWYIhU1k9BUY81LqB04pmM0mydu2WmWIvqg6PfrV',
            ],
            'nextToken': 'string'
        }
    )


    with iot_stub:
        with Client(app.app) as client:
            response = client.http.delete('/light/{}'.format(lightId))
            assert response.status_code == 204

#         if request.method == 'DELETE':
#             certARN = iot.list_thing_principals(
#                 thingName=id
#             )['principals'][0]

#             # 非同期なので、今すぐ消すことができないです。
#             detach_cert = iot.detach_thing_principal(
#                 thingName=id,
#                 principal=certARN
#             )

#             response = iot.update_thing(
#                 thingName=id,
#                 attributePayload={
#                     'attributes': {
#                         'PENDING_DELETE': 'true'
#                     },
#                     'merge': True
#                 }
#             )

#             inactivate_cert = iot.update_certificate(
#                 certificateId=certARN.split("/")[1],
#                 newStatus='INACTIVE'
#             )

#             # ハード削除を非同期にするため、SQSにMSGを送信
#             SQS = sqs.send_message(
#                 QueueUrl='https://sqs.ap-northeast-1.amazonaws.com/090509233173/deletion-queue',
#                 MessageBody=json.dumps({"certARN":certARN,"thingName":id})
#             )
#         return Response(body=None,
#                 status_code=204,
#                 headers={'Content-Type': 'application/json'})

def test_one_light_command():
    lightId = str(uuid.uuid4())
    topic = '{}/command'.format(lightId)
    iot_data_stub = Stubber(app.iot_data)

    iot_data_stub.add_response(
        'publish',
        expected_params={
            'topic': topic,
            'qos': 1,
            'payload': json.dumps({ "power": True }).encode('utf-8')
        },
        service_response={}
    )

    with iot_data_stub:
        with Client(app.app) as client:
            response = client.http.post('/light/{}/command/on'.format(lightId))
            assert response.json_body == {
                "id": lightId,
                "topic": "{}/command".format(lightId),
                "command": {
                    "power": True
                }
            }


def test_handle_sqs_message():
    lightId = str(uuid.uuid4())
    iot_stub = Stubber(app.iot)
    sqs_stub = Stubber(app.sqs)

    iot_stub.add_response(
        'delete_certificate',
        expected_params={
            'certificateId': 'a1bc234567da6bf9a06282b84313ace1b492e2e276c4d0de61f591176c000000',
            'forceDelete': True
        },
        service_response={}
    )

    iot_stub.add_response(
        'delete_thing',
        expected_params={
            'thingName': lightId
        },
        service_response={}
    )

    sqs_stub.add_response(
        'delete_message',
        expected_params={
            'QueueUrl': 'https://sqs.ap-northeast-1.amazonaws.com/090509233173/deletion-queue',
            'ReceiptHandle': 'receipt-handle'
        },
        service_response={}
    )


    with iot_stub:
        with sqs_stub:
            with Client(app.app) as client:
                message = json.dumps({
                    "certARN":"arn:aws:iot:ap-northeast-1:000000000000:cert/a1bc234567da6bf9a06282b84313ace1b492e2e276c4d0de61f591176c000000",
                    "thingName": lightId
                })

                try:
                    response = client.lambda_.invoke(
                        "handle_sqs_message",
                        client.events.generate_sqs_event([message], queue_name='deletion-queue')
                    )
                    assert response.payload == {}
                except Exception:
                    # 結果はないか処理された例外となります。じゃない場合、不合格
                    pytest.fail("Unexpected Error")