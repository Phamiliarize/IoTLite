def light(obj):
    return {
        'id': obj['thingName'],
        'connectivity': obj.get('connectivity', None)
    }


def new_device(thing, cert):
    return {
        'id': thing['thingName'],
        'cert': cert['certificatePem'],
        'publicKey': cert['keyPair']['PublicKey'],
        'privateKey': cert['keyPair']['PrivateKey'],
        'topics': [
            '{}/data'.format(thing['thingName']),
            '{}/command'.format(thing['thingName'])
        ]
    }


def command(id, payload):
    return {
        'id': id,
        'topic': '{}/command'.format(id),
        'command': payload
    }
