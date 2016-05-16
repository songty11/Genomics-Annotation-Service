from bottle import subprocess
import json
import os
import boto3
import time
import botocore
import os
import MySQLdb as mdb

# Connect to SQS and get the message queue
# Poll the message queue in a loop 
sqs = boto3.resource('sqs')
s3 = boto3.resource('s3')
queue = sqs.get_queue_by_name(QueueName='songty_results_notifications')
client = boto3.client('ses')
while True:

    # long polling
    # https://github.com/boto/boto3-sample/blob/master/transcoder.py
    host = "songty-auth-db.catcuq1wrjmn.us-east-1.rds.amazonaws.com"
    user = "songty"
    passwd = "s5468279130"
    dbname = "gasauth"
    messages = queue.receive_messages(MaxNumberOfMessages=10,WaitTimeSeconds=20)
    if len(messages) > 0:
        for message in messages:
            # http://boto3.readthedocs.io/en/latest/reference/services/sqs.html#SQS.Message.body
            data = json.loads(message.body)
            print auth.user
            job_id = data["job_id"]
            username = data["username"]
            html = "Hello, " + username + "<br /><br />\
You are receiving this email because your job <a href=https://songty.ucmpcs.org:4433/annotations/"+job_id+ ">" + job_id +"</a> has completed!<br /><br />Click the ID to see the details.<br /><br />All the best from,<br />The GAS Team"
            con = mdb.connect(host, user,passwd,dbname)
            cur = con.cursor()
            cur.execute("SELECT email_addr FROM users WHERE username = '"+ username+"'")
            val = cur.fetchone()
            email_addrs = val[0]
            con.close()
            print email_addrs
            response = client.send_email(
    Source='songty@ucmpcs.org',
    Destination={
        'ToAddresses': [
        email_addrs,
        ]
    },

    Message={
        'Subject': {
        'Data': 'Job Complete',
        'Charset': 'UTF-8'
        },
        'Body': {
            'Html': {
                'Data': html ,
                'Charset': 'UTF-8'
            }
        }
    }
)
            message.delete()