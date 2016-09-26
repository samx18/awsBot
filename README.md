#README
The AWS Slack bot allows you manage your AWS resources directly from Slack and not having to switch between the console and the AWS CLI. Since the bot is based on a serverless architecture using AWS lambda, it can scale easily. Currently it supports EC2 , S3 and Cloudformation. 


![alt tag](https://github.com/samx18/awsBot/blob/master/assets/awsBot.jpg)

Once deployed, you can get additional usage instructions by saying 

	AWS help usage

## Requirements 
* AWS account with admin access to the following
	* IAM
	* Lambda
	* EC2
	* S3
	* KMS
	* Cloudwatch
	* Cloudformation
* Slack admin account 


## Create IAM role
You will need to create a custom IAM role for your lambda functions.  Use IAM to create a new role and attach the following policies 

* AmazonS3FullAccess
* AmazonEC2FullAccess
* AWSLambdaFullAccess

You will also need a custom policy for cloudformation 

```

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:*"
            ],
            "Resource": "*"
        }
    ]
}

```

## Create Lambda Functions

Use the main.py to create your main lambda function. Choose the Python 2.7 as the language. Since it does not use any external packages other than boto3, you can directly copy paste to the inline editor.

Use the cwmain.py to create another lambda function. Again you can copy pate to the inline code editor.

Note: - You will need to update the slack outgoing url and the token in both the functions. We will do that after encrypting them using KMS.

## Create API gateway

Now head over to API gateway to create a new API
* Create a method of type: POST
* Select Integration Type: Lambda
* Select the region in which you created your Lambda function
* Select the Lambda Function you created from main.py 
* Click "Integration Request"
* At the bottom of this Page select "Add mapping Template"
* For content type please specify: "application/x-www-form-urlencoded"
Insert the template code from integrationRequest.txt. 

## Create custom integrations in Slack

Next we will create two custom integrations in Slack

* In Slack, Go to Apps and Integrations
* Click Build in the top right
* Select Make a Custom Integration
* Select Outgoing Webhooks
* Pick a trigger word for your Bot and also the channel that you want your bot to listen
* In URL, put the URL created by your API Gateway Deployment
* Make a note of the token
* Now create a incoming webhook
* Choose the channel where messages will be sent and click "Add Incoming WebHooks Integration"
* Copy the webhook URL

## Encrypt the Slack URL and Token using KMS

Next we will create a key to encrypt both the token and the incoming web hook URL using KMS

* Go to AWS KMS and create a new KMS key
* Encrypt the token and the incoming URL via the AWS CLI using the key created above

```
aws kms encrypt --key-id alias/<KMS key name> --plaintext "slack token / incoming url"

```
* Update the main.py lambda function with the encrypted token
* Update the cwmain.py lambda function with the encrypted webhook url 

