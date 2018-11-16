from slackclient import SlackClient
import json
import time, threading


email_user = {}  # email_user[email] = id
sc = None

def update_user_list():
	payload = sc.api_call(
	  "users.list",
	   presence=False
	)
	
	##for member in payload['members']:
	##	if 'email' in member['profile']:
	##		email_user[member['profile']['email'].lower()] = member['id']
			
	threading.Timer(1 * 86400, update_user_list).start()
	

def msg_to_user(email, principal_email, name, message, visit_id):
	email = email.lower()
	principal_email = principal_email.lower()

	if not email in email_user:
		if not principal_email in email_user:
			raise KeyError('No slack user found for email {0}'.format(email))
		email = principal_email

	resp = sc.api_call(
	  "chat.postMessage",
	  channel=email_user[email],
	  text=":tada:",
	  as_user=True,
	  
	  attachments=[{'text': '{name} is here at the reception to visit you. Their message: {message}.'.format(name=name, message=message), 'fallback': 'No', 'callback_id': 'reception_decision', 'color': '#3AA3E3', 'attachment_type': 'default',
					'actions': [
						{
						"name": "choice",
						"text": "Accept",
						"type": "button",
						"value": "accept {0}".format(visit_id)
						}, 
						
						{
						"name": "choice",
						"text": "Reject",
						"style": "danger",
						"type": "button",
						"value": "reject {0}".format(visit_id),
						"confirm": {
							"title": "Are you sure?",
							"text": "Are you sure you want to reject this person?",
							"ok_text": "Yes",
							"dismiss_text": "No"
							}
						}
					]
				}
			]
	)
	

def init_slack(app):
	global sc
	sc = SlackClient(app.config['SLACK_TOKEN'])
	update_user_list()





