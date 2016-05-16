# Copyright (C) 2015 University of Chicago
#
__author__ = 'Vas Vasiliadis <vas@uchicago.edu>'

import base64
import datetime
import hashlib
import hmac
import json
import sha
import string
import time
import urllib
import urlparse
import uuid
import boto3
import botocore.session
from boto3.dynamodb.conditions import Key,Attr

from mpcs_utils import log, auth
from bottle import route, request, redirect, template, static_file

'''
*******************************************************************************
Set up static resource handler - DO NOT CHANGE THIS METHOD IN ANY WAY
*******************************************************************************
'''
@route('/static/<filename:path>', method='GET', name="static")
def serve_static(filename):
  # Tell Bottle where static files should be served from
	return static_file(filename, root=request.app.config['mpcs.env.static_root'])

'''
*******************************************************************************
Home page
*******************************************************************************
'''
@route('/', method='GET', name="home")
def home_page():
	log.info(request.url)
	return template(request.app.config['mpcs.env.templates'] + 'home', auth=auth)

'''
*******************************************************************************
Registration form
*******************************************************************************
'''
@route('/register', method='GET', name="register")
def register():
	log.info(request.url)
	return template(request.app.config['mpcs.env.templates'] + 'register',
		auth=auth, name="", email="", username="", alert=False)

@route('/register', method='POST', name="register_submit")
def register_submit():
	auth.register(description=request.POST.get('name').strip(),
								username=request.POST.get('username').strip(),
								password=request.POST.get('password').strip(),
								email_addr=request.POST.get('email_address').strip(),
								role="free_user")
	return template(request.app.config['mpcs.env.templates'] + 'register', 
		auth=auth, alert=True)

@route('/register/<reg_code>', method='GET', name="register_confirm")
def register_confirm(reg_code):
	log.info(request.url)
	auth.validate_registration(reg_code)
	return template(request.app.config['mpcs.env.templates'] + 'register_confirm',
		auth=auth)

'''
*******************************************************************************
Login, logout, and password reset forms
*******************************************************************************
'''
@route('/login', method='GET', name="login")
def login():
	log.info(request.url)
	redirect_url = "/annotations"
	# If the user is trying to access a protected URL, go there after auhtenticating
	if request.query.redirect_url.strip() != "":
		redirect_url = request.query.redirect_url

	return template(request.app.config['mpcs.env.templates'] + 'login', 
		auth=auth, redirect_url=redirect_url, alert=False)

@route('/login', method='POST', name="login_submit")
def login_submit():
	auth.login(request.POST.get('username'),
						 request.POST.get('password'),
						 success_redirect=request.POST.get('redirect_url'),
						 fail_redirect='/login')

@route('/logout', method='GET', name="logout")
def logout():
	auth.require(fail_redirect='/')
	log.info(request.url)
	auth.logout(success_redirect='/login')


'''
*******************************************************************************
Core GAS code is below...
*******************************************************************************
'''

'''
*******************************************************************************
Subscription management handlers
*******************************************************************************
'''
import stripe

# Display form to get subscriber credit card info
@route('/subscribe', method='GET', name="subscribe")
def subscribe():
	auth.require(fail_redirect='/')
	return template(request.app.config['mpcs.env.templates'] + 'subscribe',auth=auth,alert = False,invalid = False)

# Process the subscription request
@route('/subscribe', method='POST', name="subscribe_submit")
def subscribe_submit():
	auth.require(fail_redirect='/')
	try:
		token=request.POST.get('stripe_token').strip()
		stripe.api_key = request.app.config ['mpcs.stripe.secret_key']
		customer = stripe.Customer.create(
	  card = token,
	  plan = "premium_plan",
	  email = auth.current_user.email_addr,
	  description = auth.current_user.username)
		auth.current_user.update(role="premium_user")
		s3 = boto3.resource('s3')
		bucket = s3.Bucket('gas-archive')
		for obj_sum in bucket.objects.all().filter(Prefix='songty/'+auth.current_user.username):
			obj = s3.Object(obj_sum.bucket_name, obj_sum.key)
			if obj.storage_class == "GLACIER":
				resp = bucket.meta.client.restore_object(Bucket=obj_sum.bucket_name,Key=obj_sum.key,RestoreRequest={'Days': 1})
				
		return template(request.app.config['mpcs.env.templates'] + 'subscribe',auth=auth,alert = True,invalid = False)
	except:
		return template(request.app.config['mpcs.env.templates'] + 'subscribe',auth=auth,alert = False,invalid = True)


'''
*******************************************************************************
Display the user's profile with subscription link for Free users
*******************************************************************************
'''
@route('/profile', method='GET', name="profile")
def user_profile():
	auth.require(fail_redirect='/')
	return template(request.app.config['mpcs.env.templates'] + 'profile',auth=auth)


'''
*******************************************************************************
Creates the necessary AWS S3 policy document and renders a form for
uploading an input file using the policy document
*******************************************************************************
'''
@route('/annotate', method='GET', name="annotate")
def upload_input_file():
	auth.require(fail_redirect='/')
	redirect_url = str(request.url)+"/job"
	encrypt = "AES256"
	time = datetime.timedelta(days = 1) + datetime.datetime.today();
	# define S3 policy document 
	policy = {"expiration":time.strftime('%Y-%m-%dT%H:%M:%S.000Z'), 
	    "conditions": 
	    [{"bucket":"gas-inputs"},
	    {"acl": "private"},
	    {"x-amz-server-side-encryption":encrypt},
	    ["starts-with", "$key", "songty/"],
	    ["starts-with", "$success_action_redirect",redirect_url],
	    ]
	    }
	s3_key = str(uuid.uuid4())
	#https://docs.python.org/2/library/base64.html
	Policy_Code = base64.b64encode(str(policy)).encode('utf8')

	session = botocore.session.get_session()
	credentials = session.get_credentials()
	access_key = credentials.access_key
	secret_key = credentials.secret_key

	#https://docs.python.org/2/library/hmac.html
	my_hmac = hmac.new(secret_key.encode(),Policy_Code,hashlib.sha1)
	digest = my_hmac.digest()
	signature = base64.b64encode(digest)
	return template(request.app.config['mpcs.env.templates'] + 'upload',auth=auth, acl ="private",encryption=encrypt,policy = Policy_Code, aws_access_key_id = access_key,signature = signature,redirect_url = redirect_url,s3_key_name = "songty/" + s3_key)


'''
*******************************************************************************
Accepts the S3 redirect GET request, parses it to extract 
required info, saves a job item to the database, and then
publishes a notification for the annotator service.
*******************************************************************************
'''
@route('/annotate/job', method='GET')
def create_annotation_job_request():
	auth.require(fail_redirect='/')
	formdata = request.query
	key = formdata["key"]
	file_name = key.split("/")[-1]
	job_id = file_name.split("~")[0]
	sqs = boto3.resource('sqs')
	data = {"job_id": str(job_id),
	        "username": auth.current_user.username,
	        "s3_inputs_bucket": "gas-inputs",
	        "s3_key_input_files": key,
	        "input_file_name": file_name.split("~")[1],
	        "submit_time": int(time.time()),
	        "job_status": "PENDING"
	        }

	dynamodb = boto3.resource('dynamodb')
	ann_table = dynamodb.Table('songty_annotations')
	ann_table.put_item(Item=data)

	#http://boto3.readthedocs.io/en/latest/reference/services/sqs.html#queue
	queue = sqs.get_queue_by_name(QueueName='songty_job_requests')
	queue.send_message(MessageBody=json.dumps(data))

	return template(request.app.config['mpcs.env.templates'] + 'upload_confirm',
		auth=auth,job_id=job_id)


'''
*******************************************************************************
List all annotations for the user
*******************************************************************************
'''
@route('/annotations', method='GET', name="annotations_list")
def get_annotations_list():
	auth.require(fail_redirect='/')
	username = auth.current_user.username
	dynamodb = boto3.resource('dynamodb')
	ann_table = dynamodb.Table('songty_annotations')
	response = ann_table.scan(
    FilterExpression=Attr('username').eq(username)
)
	items = response["Items"]
	for i in items:
		timestamp = i["submit_time"]
		time_tuple = time.localtime(timestamp)
		date_str = time.strftime("%Y-%m-%d %H:%M", time_tuple)
		i["submit_time"] = date_str
	return template(request.app.config['mpcs.env.templates'] + 'annotations_list',
                auth=auth,item = items)


'''
*******************************************************************************
Display details of a specific annotation job
*******************************************************************************
'''
@route('/annotations/<job_id>', method='GET', name="annotation_details")
def get_annotation_details(job_id):
	auth.require(fail_redirect='/')
	dynamodb = boto3.resource('dynamodb')
	ann_table = dynamodb.Table('songty_annotations')
	response = ann_table.scan(FilterExpression=Attr('job_id').eq(job_id))

	timestamp = response["Items"][0]["submit_time"]
	time_tuple = time.localtime(timestamp)
	request_date_str = time.strftime("%Y-%m-%d %H:%M", time_tuple)
	status = response["Items"][0]["job_status"]
	complete_date_str = ""
	is_over = False
	if status == "COMPLETE":
		timestamp = response["Items"][0]["complete_time"]
		time_tuple = time.localtime(timestamp)
		complete_date_str = time.strftime("%Y-%m-%d %H:%M", time_tuple)
		current_time = int(time.time()) 
		if current_time - response["Items"][0]["complete_time"] >= 7200:
			is_over = True

	input_file_key = "songty/"+job_id+"~"+response["Items"][0]["input_file_name"]
	result_file_key = "songty/"+job_id+"~"+response["Items"][0]["input_file_name"].split('.')[0]+".annot.vcf"
	 #https://github.com/boto/boto3/issues/110 
	session = botocore.session.get_session()
	client = session.create_client('s3')
	input_file_url = client.generate_presigned_url(
    'get_object', Params={'Bucket': "gas-inputs", 'Key':input_file_key})
	result_file_url = client.generate_presigned_url(
    'get_object', Params={'Bucket': "gas-results", 'Key':result_file_key})

	
	
	return template(request.app.config['mpcs.env.templates'] + 'annotation_details',auth=auth,request_id = job_id, request_time = request_date_str, input_file = response["Items"][0]["input_file_name"],status=response["Items"][0]["job_status"],complete_time=complete_date_str,input_url = input_file_url,result_url = result_file_url,over_hours = is_over)


'''
*******************************************************************************
Display the log file for an annotation job
*******************************************************************************
'''
@route('/annotations/<job_id>/log', method='GET', name="annotation_log")
def view_annotation_log(job_id):
	auth.require(fail_redirect='/')
	dynamodb = boto3.resource('dynamodb')
	ann_table = dynamodb.Table('songty_annotations')
	response = ann_table.scan(FilterExpression=Attr('job_id').eq(job_id))
	file_name = response["Items"][0]["input_file_name"]
	bucket_name = "gas-results"
	key = "songty/" + job_id +"~"+file_name + ".count.log"

	s3 = boto3.resource('s3')
	object = s3.Object(bucket_name,key)
	content = object.get()["Body"].read().split('\n')

	return template(request.app.config['mpcs.env.templates'] + 'annotation_log',
	    auth=auth,content = content)




### EOF