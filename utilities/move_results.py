from bottle import subprocess
import json
import os
import boto3
import time
import botocore
import os
import MySQLdb as mdb
from boto3.dynamodb.conditions import Key,Attr

# Connect to SQS and get the message queue
# Poll the message queue in a loop 
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
bucket = s3.Bucket('gas-archive')
# http://zetcode.com/db/mysqlpython/
host = "songty-auth-db.catcuq1wrjmn.us-east-1.rds.amazonaws.com"
user = "songty"
passwd = "s5468279130"
dbname = "gasauth"

try:
    con = mdb.connect(host, user, passwd, dbname)
    while True:
		cur = con.cursor()
		cur.execute("SELECT username FROM users WHERE role = 'premium_user'")
		table = dynamodb.Table('songty_annotations')
		# https://github.com/boto/boto3/issues/380
		if not cur == None:
			for user in cur:
				for obj_sum in bucket.objects.all().filter(Prefix='songty/'+user[0]):
					obj = s3.Object(obj_sum.bucket_name, obj_sum.key)
					if obj.storage_class !="GLACIER":
						s3.Object('gas-results','songty/'+obj.key.split('#')[-1]).copy_from(CopySource='gas-archive/'+obj.key)
						s3.Object('gas-archive',obj.key).delete()
						if obj.key.split('.')[-1] == 'cvf':
							table.update_item(Key={"job_id": obj.key.split('#')[-1].split('~')[0]}, 
		                            UpdateExpression="set s3_results_bucket = :s3s,\
		                            s3_key_result_file = :resF",
		                            ExpressionAttributeValues={
		                                ":s3s": "gas-results",
		                                ":resF": "songty/" + obj.key.split('#')[-1]
		                            })

						else:
							table.update_item(Key={"job_id": obj.key.split('#')[-1].split('~')[0]}, 
		                            UpdateExpression="set s3_results_bucket = :s3s,\
		                            s3_key_log_file = :logF",
		                            ExpressionAttributeValues={
		                                ":s3s": "gas-results",
		                                ":logF": "songty/" + obj.key.split('#')[-1]
		                            })
						print 'move gas-archive/'+ obj.key + "to" + 'gas-results/songty/' + obj.key.split('#')[-1]
		time.sleep(10)

except mdb.Error, e:
	print "Error %d: %s" % (e.args[0],e.args[1])
	sys.exit(1)
finally:       
	if con:    
		con.close()