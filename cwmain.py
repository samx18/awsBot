'''
Follow these steps to configure the webhook in Slack:

  1. Navigate to https://<your-team-domain>.slack.com/services/new

  2. Search for and select "Incoming WebHooks".

  3. Choose the default channel where messages will be sent and click "Add Incoming WebHooks Integration".

  4. Copy the webhook URL from the setup instructions and use it in the next section.


Follow these steps to encrypt your Slack hook URL for use in this function:

  1. Create a KMS key - http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html.

  2. Encrypt the event collector token using the AWS CLI.
     $ aws kms encrypt --key-id alias/<KMS key name> --plaintext "<SLACK_HOOK_URL>"

     Note: You must exclude the protocol from the URL (e.g. "hooks.slack.com/services/abc123").

  3. Copy the base-64 encoded, encrypted key (CiphertextBlob) to the ENCRYPTED_HOOK_URL variable.

  4. Give your function's role permission for the kms:Decrypt action.
     Example:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1443036478000",
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": [
                "<your KMS key ARN>"
            ]
        }
    ]
}
'''
from __future__ import print_function

import boto3
import json
import logging

from base64 import  b64decode
from urllib2 import  Request, urlopen, URLError, HTTPError

# Replace this with your encrypted slack token before deploying.
# Encrypt the slack token using KMS to prevent unauthorized access.
ENCRYPTED_HOOK_URL = 'AQECAHgT/MsA4/sL3S5flIV8eLI13GPSUwLOdlMiunWVHtJm/QAAAKcwgaQGCSqGSIb3DQEHBqCBljCBkwIBADCBjQYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAxe4oSzOdFIdFOunHYCARCAYMZU9PoYrTUEAkey+GCXqLTTmNpECB2Sh6CY0hwh1b2gV3+0GxRMwtvZiNYltvSXjR2pY2qoxxmXfxH54jzsOBUNOtICPzj4onrmbmd6d4nfMiLtuGUwT1rwctPIHifCKQ=='

SLACK_CHANNEL = 'bot-testing'

HOOK_URL = "https://" + boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_HOOK_URL))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    state = event['detail']['state']
    instance = event['detail']['instance-id']
    #region = event['region']
    
    logger.info("Event: " + str(event))

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
