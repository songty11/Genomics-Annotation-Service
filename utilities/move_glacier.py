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
# http://zetcode.com/db/mysqlpython/
host = "songty-auth-db.catcuq1wrjmn.us-east-1.rds.amazonaws.com"
user = "songty"
passwd = "s5468279130"
dbname = "gasauth"

try:
    con = mdb.connect(host, user, passwd, dbname)
    while True:
		cur = con.cursor()
		cur.execute("SELECT username FROM users WHERE role = 'free_user'")
		for user in cur:
			table = dynamodb.Table('songty_annotations')
			response = table.scan(FilterExpression=Attr('username').eq(user[0]))
			for item in response["Items"]:
				if item["job_status"] == "COMPLETE":
					current_time = int(time.time())
					complete_time = item["complete_time"]
					if current_time - complete_time >7200 and item["s3_results_bucket"] =="gas-results":
						
						log_file = item["s3_key_log_file"]
						res_file = item["s3_key_result_file"]
						log_path = user[0]+"#" + log_file.split('/')[-1]
						res_path = user[0]+"#" + res_file.split('/')[-1]
						s3.Object('gas-archive','songty/'+res_path).copy_from(CopySource='gas-results/'+res_file)
						s3.Object('gas-archive','songty/'+log_path).copy_from(CopySource='gas-results/'+log_file)
						s3.Object('gas-results',log_file).delete()
						s3.Object('gas-results',res_file).delete()
						table.update_item(Key={"job_id": item['job_id']}, 
	                            UpdateExpression="set s3_results_bucket = :s3s,\
	                            s3_key_result_file = :resF,\
	                            s3_key_log_file = :logF",
	                            ExpressionAttributeValues={
	                                ":s3s": "gas-archive",
	                                ":resF": "songty/" + res_path,
	                                ":logF": "songty/" + log_path
	                            })
						print "move gas-results/" + res_file +"to gas-archive/songty/" +  res_path
						print "move gas-results/" + log_file +"to gas-archive/songty/" +  log_path
		time.sleep(10)

except mdb.Error, e:
	print "Error %d: %s" % (e.args[0],e.args[1])
	sys.exit(1)
finally:       
	if con:    
		con.close()