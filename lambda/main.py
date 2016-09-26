from __future__ import print_function
import logging
import boto3
import botocore
from base64 import b64decode

log = logging.getLogger()
log.setLevel(logging.DEBUG)

aws_regions=['us-east-1','ap-south-1','us-west-1','us-west-2','ap-northeast-2',\
'ap-southeast-1','ap-southeast-2','ap-northeast-1','eu-central-1','eu-west-1','sa-east-1']
aws_services=['ec2','s3']

def bot_help(service, option):
    if service == 'usage':
        h = "Hello, I am your friendly AWS bot. I am currently trained to work with EC2, S3 and Cloudformation.\n Here are a few examples of what I can do \n"
        h = h+"*List the status of your instance in a region* :  `AWS list ec2 us-west-2` \n"
        h = h+"*Start an instance* : `AWS start id00000000 us-west-2` \n"
        h = h+"*Stop an instance* : `AWS stop id55555555 us-west-2` \n"
        h = h+"*Backup an instance* : `AWS backup id55555555 us-west-2` \n"
        h = h+"*Get backup information for an instance* : `AWS backup-info id55555555 us-west-2` \n"
        h = h+"*List S3 buckets* : `AWS list s3` \n"
        h = h+"*List contents of a bucket* : `AWS list s3 mytestbucket` \n"
        h = h+"*Create and deploy a resources using Cloudformation* : `AWS create stackname https://s3templateurl`"
    else:
        h = ":exclamation:Available commands `{0}`\n".format(commands.keys())
        h += "Usage: `AWS <command> <service or ID or arn> <option or region>` \n *You can also get additional usage examples by saying* `AWS help usage`"
    return h

def list_details(service,option):
    service = service.lower()
    option = option.lower()
    if service == "none" or service not in aws_services:
        text = ":rotating_light: Sorry, I did not understand that service. Currently I only support  EC2 and S3 services.\
\n Usage: `AWS list <instance> <region>`\n Example: `AWS list ec2 us-west-2`"
    elif service == 'ec2' and option == "none":
        text = ":rotating_light: Sure I can do that, but I need to know the region name. \n Usage: `AWS list instance <region>`\n Example: `AWS list ec2 us-west-2`"
    elif service == 'ec2' and option not in aws_regions:
    	text = ":rotating_light: Sorry, I don't understand that region. Currently supported regions are: \n `"+', '.join(aws_regions)+"`"
    elif service == 's3':
        s3 = boto3.resource('s3')
        bucketName = []
        for bucket in s3.buckets.all():
            bucketName.append(bucket.name)
        if option == "none":
            for b in bucketName:
                h = '\n'.join(bucketName)
                text = "Listing all your buckets by name:\n ```"+h+"```"
        elif option not in bucketName:
            text = ":rotating_light: Ah! That looks like an invalid bucket name\n Usage: `AWS list s3 <bucketname>`"
        else:
            objectName =[]
            bucket = s3.Bucket(option)
            # Handle for empty buckets
            h="Empty Bucket"
            text = "Listing objects in bucket *"+option+"* \n```"+h+"```"
            for obj in bucket.objects.all():
                objectName.append(obj.key)
            for b in objectName:
                h = '\n'.join(objectName)
                text = "Listing objects in bucket *"+option+"* \n```"+h+"```"
    else:
        ec2 = boto3.resource('ec2', region_name=option)
        instances = ec2.instances.all()
        runningInst=[]
        stoppedInst=[]
        i= "None"
        j = "None"
        for i in instances:
            if i.state['Name'] == 'running':
                runningInst.append(i.id)
            elif i.state['Name'] == 'stopped':
                stoppedInst.append(i.id)
        for i in runningInst:
            j='\n'.join(runningInst)
        for i in stoppedInst:
            k='\n'.join(stoppedInst)
        text=  "Listing your instance status for "+option+"\n" "*Running:* \n" +"```"+j+"```"+"\n *Stopped:* \n" + "```"+k+"```"
    return text


def validate(service,option):
    val = 1
    text = "Opps something whent worng that even I could not handle"
    if option == 'none' or service == 'none':
        text = ":rotating_light: Sure I can do that, but  I need an instance ID and a region\n Usage: `AWS <start/stop/backup/backup-info> <instance ID> <region>`\n Example: `AWS start id00000000 us-west-2`"
        val = 0
    elif option not in aws_regions:
        text =":rotating_light: Sorry, I don't understand that region. Currently supported regions are: \n `"+', '.join(aws_regions)+"`"
        val = 0
    else:
        ec2 = boto3.resource('ec2', region_name=option)
        instances = ec2.instances.all()
        #Validate instance ID
        idList = []
        for i in instances:
            idList.append(i.id)
        if service not in idList:
            text = ":rotating_light: Sorry, I do not recognize that instance ID or the instance might be in a different region\n \
Usage: `AWS <start/stop/backup/backup-info> <instance ID> <region>`\n Example: `AWS start id00000000 us-west-2`"
            val = 0
    return text, val
    


def start(service,option):
    text,val = validate(service,option)
    if val == 1:
        client = boto3.client('ec2',region_name=option)
        instanceID=[service]
        instanceDetails = client.describe_instance_status(InstanceIds=instanceID)
        state = 'stopped'
        for each in instanceDetails["InstanceStatuses"]:
            state = each["InstanceState"]["Name"]
        if state == 'running':
            text = "The instance `" + service +"` is already running! Nothing much for me to do... :simple_smile:"
        else:
            client.start_instances(InstanceIds=instanceID)
            text = "Starting your instance with id `"+ service +"` in the region `"+option+"`"
    return text



def stop(service,option):
    text,val = validate(service,option)
    if val == 1:
        client = boto3.client('ec2',region_name=option)
        instanceID=[service]
        instanceDetails = client.describe_instance_status(InstanceIds=instanceID)
        state = 'stopped'
        for each in instanceDetails["InstanceStatuses"]:
            state = each["InstanceState"]["Name"]
        if state != 'running':
            text = "The instance `" + service +"` is already down! Nothing much for me to do... :simple_smile:"
        else:
            client.stop_instances(InstanceIds=instanceID)
            text = "Stopping your instance with id `"+ service +"` in the region `"+option+"`"
    return text



def backup(service,option):
    text,val = validate(service,option)    
    if val == 1:
        ec2 = boto3.resource('ec2', region_name=option)
        inst2snap = ec2.Instance(id=service)
        volumes = inst2snap.volumes.all()
        temp =[]
        for volume in volumes:
            snap = volume.create_snapshot(Description='Snapshot by AWS Bot')
            temp.append("\n Snapshot for volume with ID `" + volume.id + "` is in progress.")
        text = ' '.join(temp)
        text = "Backup started for instance with ID `" + service + "` " +text
    return text

def backupinfo(service,option):
    text,val = validate(service,option)
    if val == 1:
        ec2 = boto3.resource('ec2', region_name=option)
        instance = ec2.Instance(id=service)
        volumes = instance.volumes.all()
        h = "Backup information for instance `" + service +"`\n"
        for volume in volumes:
            h = h+"Attached volume `" + volume.id +"`\n"
            snap = 0
            for s in volume.snapshots.all():
                h = h+"Avilable snapshots for `" + volume.id + "` snapshot ID `"+ s.id + "` \
status `" +  s.state+ "` on `" + str(s.start_time.date())+ "` at `"+str(s.start_time.time())+ "`\n"
                snap = 1
            if snap == 0:
                h = h + "There are no available snapshots for this volume! \n"
        text = h
    return text

def create(service,option):
    if service == "none" or option == "none":
        text = ":rotating_light: Sure, I can create resources for you using Cloudformation, but I need both a stack name & a template url from S3 \n \
Usage: `AWS create  <stackname> <template s3 url>`\n Example: `AWS create mystack https://s3-us-west-2.amazonaws.com/xxxxx/xxx.json`"
    else:
        option = option[1:-1]
        client = boto3.client('cloudformation')
        try:
            client.create_stack(StackName=service,TemplateURL=option)
            text =  "Oh Happy Day! Your stack was created and the resources you requested are being deployed :rocket: Hang on tight...."
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                text = ":rotating_light: A stack by that name already exists.\n" + "Usage: `AWS create <stack name> <template S3 URL>`"
            elif e.response['Error']['Code'] == 'ValidationError':
                text = ":rotating_light: Sorry, I am having trouble with the  template URL you mentioned. \
You may want to verify the template S3 URL and permessions \n" + "Usage: `AWS create  <stack name> <template S3 URL>` \n Example: `AWS create demostack  https://s3-us-west-2.amazonaws.com/xxxxx/xxx.json`"
            else:
                text = "Unexpected Error: As awesome as I am, even I am unable to make sense of this error"
    return text


commands = {
    'help': bot_help,
    'list': list_details,
    'create': create,
    'stop': stop,
    'start': start,
    'backup': backup,
    'backup-info': backupinfo
}


def lambda_handler(event,context):
    assert context
    # Replace this with your encrypted slack token before deploying.
    # Encrypt the slack token using KMS to prevent unauthorized access.
    ENCRYPTED_EXPECTED_TOKEN = 'AQECAHgT/MsA4/sL3S5flIV8eLI13GPSUwLOdlMiunWVHtJm/QAAAHYwdAYJKoZIhvcNAQcGoGcwZQIBADBgBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDCfTRlU5bV0Mws1yLwIBEIAzjGu4jtdVhJGklyCMBZlwtlzL7ANUYiKak1VxjTvM8ZDuLYx7loYdctKw6By/C/3ZRZQa'  # Enter the base-64 encoded, encrypted Slack command token (CiphertextBlob)
    kms = boto3.client('kms')
    expected_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']
    token = event['token']
    if token != expected_token:
        return
    
    log.debug(token)
    log.debug(event)
    bot_event = event

    trigger_word = bot_event['trigger_word']
    raw_text = bot_event['text']
    raw_args = raw_text.replace(trigger_word, '',1).strip()

    args = raw_args.split()
    log.debug("[lambda_handler] args:{0}".format(args))

    service = "none"
    option = "none"
    
   
    if len(args) == 0 or len(args) > 3 or args[0].lower() not in commands:
        command = 'help'
    elif len(args) == 1:
        command = args[0].lower()
    elif len(args) == 2:
        command = args[0].lower()
        service = args[1].lower()
    elif len(args) == 3:
        command = args[0].lower()
        service = args[1].lower()
        option = args[2].lower()

    resp = commands[command](service,option)

    return {
        'text': "{0}".format(resp)
    }
