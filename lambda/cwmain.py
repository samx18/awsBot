from __future__ import print_function

import boto3
import json
import logging

from base64 import  b64decode
from urllib2 import  Request, urlopen, URLError, HTTPError

# Replace this with your encrypted slack token before deploying.
# Encrypt the slack token using KMS to prevent unauthorized access.
ENCRYPTED_HOOK_URL = 'AQECAHgT/MsA4/sL3S5flIV8eLI13GPSUwLOdlMiunWVHtJm/QAAAKcwgaQGCSqGSIb3DQEHBqCewqjkhhdsaNcvpwhgalpPcG/zOdFIdFOunHYCARCAYMZU9PoYrTUEAkey+GCXqLTTmNpECB2Sh6CY0hwh1b2gV3+0GxRMwtvZiNYltvSXjR2pY2qoxxmXfxH54jzsOBUNOtICPzj4onrmbmd6d4nfMiLtuGUwT1rwctPIHifCKQ=='

SLACK_CHANNEL = 'bot-testing' # Replace with your channel name

HOOK_URL = "https://" + boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_HOOK_URL))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    state = event['detail']['state']
    instance = event['detail']['instance-id']

    logger.info("Event: " + str(event))

    if state == 'pending':
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': "Initiating startup for instance with ID ` %s `" % (instance)
        }
    elif state == 'stopping':
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': "Initiating the shutdown for instance with ID ` %s `" % (instance)
        }
    elif state == 'running':
        client = boto3.client('ec2',region_name='us-west-2')
        instanceDetails = client.describe_instances(InstanceIds=[instance])
        if 'Association' in instanceDetails['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]:
            publicIP = instanceDetails['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']
            slack_message = {
                'channel': SLACK_CHANNEL,
                'text': "The instance ` %s ` is now in a ` %s ` state with public IP ` %s `" % (instance,state,publicIP)
            }
        else:
            slack_message = {
                'channel': SLACK_CHANNEL,
                'text': "The instance ` %s ` is now in a ` %s ` state" % (instance,state)
            }
    else:
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': "The instance ` %s ` is now in a ` %s ` state" % (instance,state)
        }

    req = Request(HOOK_URL, json.dumps(slack_message))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
