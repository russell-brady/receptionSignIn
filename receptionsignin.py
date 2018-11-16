from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
from flask_mail import Message
from flask_mail import Mail
import ldap
import json
from re import escape
from database import db, Visit, register_db
import slack


app = Flask(__name__)
Bootstrap(app)
app.config.from_object('config')
register_db(app)
slack.init_slack(app)

@app.route('/')
@app.route('/index')
def index():
	scope = request.args.get('location')
	if not scope or scope.lower() not in ['dublin', 'whatever']:
		return "You need to specify a valid location."
		
 	return render_template("index.html", scope = scope)
 
 
@app.route('/autocomplete', methods=['GET'])
def autocomplete():	
	search = request.args.get('q')
	scope = request.args.get('scope')
	querRes = query(search, 'name', scope)
	
	return jsonify(res=querRes)
 
 
@app.route('/photo', methods=['POST'])
def photo():
	if not set(['scope', 'name', 'email', 'mobile', 'visit']).issubset(request.form):
			return 'Missing params.'

	return render_template("photo.html", **request.form.to_dict())
	
	
@app.route('/person', methods=['POST'])
def person():
	if not set(['scope', 'image', 'name', 'email', 'mobile', 'visit', 'height', 'width']).issubset(request.form):
		return 'Missing params.'

	return render_template("person.html", **request.form.to_dict())


@app.route('/send', methods=['POST'])
def send():
	if not set(['image1', 'scope', 'mess', 'person', 'name', 'email', 'mobile', 'visit', 'height', 'width']).issubset(request.form):
			return 'Missing params.'

	mail = Mail(app)
	
	img = request.form.get("image1")
	scope = request.form.get("scope")
	message = request.form.get("mess")
	receiver = request.form.get("person")
	name = request.form.get("name")
	em = request.form.get("email")
	mobile = request.form.get("mobile")
	visit = request.form.get("visit")
	height = request.form.get("height")
	width = request.form.get("width")
	recipient = query(receiver, 'mail', scope)[0]
	recipientPrincipal = query(receiver, 'userPrincipalName', scope)[0]
	
	vistObj = Visit(name, em, mobile, visit, receiver, message, img, scope)
	app.logger.debug(vistObj.name)
	db.session.add(vistObj)
	db.session.commit()
	
	idRef = vistObj.id
	slack.msg_to_user(recipient, recipientPrincipal, name, message, idRef)
	
	msg = Message('Reception Visitor', sender="Jacek.Garbiec@synchronoss.com", recipients=[recipient], reply_to = em)
	msg.html = render_template("email.html", image = img,
											 name = name, 
											 mobile = mobile, 
											 visit = visit, 
											 message = message, 
											 link = "https://192.168.3.184:5000/getImage?id="+str(idRef)+"&width="+str(width)+"&height="+str(height))
	mail.send(msg)

	
	return render_template("success.html", image = img, 
										   person = receiver,
										   mobile = mobile, 
										   visit = visit, 
										   message = message, 
										   link = "https://192.168.3.184:5000/getImage?id="+str(idRef)+"&width="+str(width)+"&height="+str(height))
		
		
@app.route('/getImage', methods=['GET'])
def getImage():
	height = request.args.get("height")
	width = request.args.get("width")
	idRef = request.args.get("id")
	
	image = Visit.query.filter_by(id=idRef).first().image
	
	return render_template("image.html", image = image, width = int(width), height = int(height) )
	
	
@app.after_request  # prevent clickjacking
def apply_caching(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
	
	
def query(q, attr, scope):
	try:
		l = ldap.open(app.config['LDAP_URL'])
		l.protocol_version = ldap.VERSION3
		l.set_option(ldap.OPT_REFERRALS, 0)
		l.simple_bind_s(app.config['LDAP_USER'], app.config['LDAP_PASS'])
	except ldap.LDAPError as e:
		print e

	baseDN = 'ou={scope}, ou=Corporate, dc=synchronoss, dc=net'.format(scope=scope)
	searchScope = ldap.SCOPE_SUBTREE
	searchFilter = 'name=*{q}*'.format(q=q)
	retrieveAttributes = [attr] 

	
	result_set = []
	try:
		result_id = l.search(baseDN, searchScope, searchFilter, retrieveAttributes)
		
		while True:
			result_type, result_data = l.result(result_id, 0)
			
			if not result_data:
				break
			else: 
				if result_type == ldap.RES_SEARCH_ENTRY:
					result_set.append(result_data)
			
	except ldap.LDAPError as e:
		print e
	
	result = [x[0][1][attr][0] for x in result_set]
	return result
	
	
@app.route('/slackresponse', methods=['POST'])
def slackresponse():
	res = json.loads(request.form['payload'])

	decision, visit_id = res['actions'][0]['value'].split(' ')
	name = Visit.query.filter_by(id=visit_id).first().name
	scope = Visit.query.filter_by(id=visit_id).first().scope
	
	if decision == 'accept':
		return 'Please welcome {0} at the reception'.format(name)
	elif decision == 'reject':
		return 'Rejected {0} at the reception. The receptionist will be notified.'.format(name)
	
	

	
app.run(debug=True, host='127.0.0.1')
# app.run(debug=False, host='0.0.0.0')