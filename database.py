from flask_sqlalchemy import SQLAlchemy
import datetime


db = SQLAlchemy()


class Visit(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=False)
	email = db.Column(db.String(120), unique=False)
	mobile = db.Column(db.String(80), unique=False)
	purpose = db.Column(db.String(120), unique=False)
	person = db.Column(db.String(80), unique=False)
	message = db.Column(db.String(6000), unique=False)
	image = db.Column(db.String(120000), unique=False)
	scope = db.Column(db.String(100), unique=False)
	created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)


	def __init__(self, name, email, mobile, purpose, person, message, image, scope):
		self.name = name
		self.email = email
		self.mobile = mobile
		self.purpose = purpose
		self.person = person
		self.message = message
		self.image = image
		self.scope = scope
	   

	def __repr__(self):
		return '<User %r>' % self.username
		
		
def register_db(app):
	with app.app_context():
		db.init_app(app)
		db.create_all()