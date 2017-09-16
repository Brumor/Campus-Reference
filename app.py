from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Subcategory, User, Chapter, PersonalChapter, Discussion, DiscussionMessage, \
	ChapterExercice, ChapterHistoric
from datetime import datetime
import os
from flask import session as login_session
import random
import string
import httplib2
import json
from flask import make_response

app = Flask(__name__)


engine = create_engine('postgresql:///mainCR.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login', methods=['GET','POST'])
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
					for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['GET','POST'])
def fbconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = request.data
	
	app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
	app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
		app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	
	userinfo_url = "https://graph.facebook.com/v2.8/me"
	token = result.split(',')[0].split(':')[1].replace('"', '')
	
	url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	
	print "url sent for API access:%s" % url
	print "API JSON result: %s" % result
	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data['name']
	login_session['email'] = data["email"]
	login_session['user_id'] = data["id"]
	login_session['access_token'] = token
	login_session['access_token'] = token
	
	# Get user picture
	url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)
	
	login_session['picture'] = data["data"]["url"]
	
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id
	
	# Get user picture
	url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)
	
	login_session['picture'] = data["data"]["url"]
	
	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	
	flash("Now logged in as %s" % login_session['username'])
	return output


@app.route('/disconnect')
def disconnect():
	if 'provider' in login_session:
		if login_session['provider'] == 'facebook':
			fbdisconnect()
		del login_session['user_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['provider']
		flash("You have successfully been logged out.")
		return redirect(url_for('mainmenu'))
	else:
		flash("You were not logged in!")
		redirect(url_for('mainmenu'))


@app.route('/fbdisconnect')
def fbdisconnect():
	facebook_id = login_session['user_id']
	# The access token must me included to successfully logout
	access_token = login_session['access_token']
	url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
	h = httplib2.Http()
	result = h.request(url, 'DELETE')[1]
	return "you have been logged out"


@app.route('/', methods=['GET','POST'])
def mainmenu():
	
	if 'email' in login_session:
		user_id = getUserID(login_session['email'])
		if not user_id:
			createUser(login_session)
	
	if request.method == 'POST':
		newCategory = Category(name=request.form['name'])
		session.add(newCategory)
		session.commit()
		return redirect(url_for('mainmenu'))
	else:
		categories = session.query(Category).all()
		if 'user_id' in login_session:
			user = getUserInfo(login_session['user_id'])
			return render_template("menu_main.html", categories=categories, user=user)
		return render_template("menu_main.html", categories=categories)


@app.route('/<int:category_id>', methods=['GET','POST'])
def category_menu(category_id):
	if request.method == 'POST':
		newSubcategory = Subcategory(name=request.form['name'], category_id=category_id)
		session.add(newSubcategory)
		session.commit()
		return redirect(url_for('category_menu', category_id=category_id))
	else:
		subcategories = session.query(Subcategory).filter_by(category_id=category_id).all()
		if 'user_id' in login_session:
			user = getUserInfo(login_session['user_id'])
			return render_template('menu_category.html', category_id=category_id, subcategories=subcategories,
								   user=user)
		return render_template('menu_category.html', category_id=category_id, subcategories=subcategories)


@app.route('/<int:category_id>/<int:subcategory_id>')
def subcategory_menu(category_id, subcategory_id):
	articles = session.query(Chapter).filter_by(subcategory_id=subcategory_id).all()
	if 'user_id' in login_session:
		user = getUserInfo(login_session['user_id'])
		return render_template('menu_subcategory.html', category_id=category_id, subcategory_id=subcategory_id,
							   articles=articles, user=user)
	return render_template('menu_subcategory.html', category_id=category_id, subcategory_id=subcategory_id,
						   articles=articles)


@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/main')
def article_main(category_id, subcategory_id, article_id):
	article = session.query(Chapter).filter_by(id=article_id).one()
	if 'user_id' in login_session:
		user = getUserInfo(login_session['user_id'])
		return render_template('chapter_main.html', category_id=category_id, subcategory_id=subcategory_id,
							   article_id=article_id, article=article, user=user)
	return render_template('chapter_main.html', category_id=category_id, subcategory_id=subcategory_id,
						   article_id=article_id, article=article)


@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/discussions', methods=['GET','POST'])
def article_discussion(category_id, subcategory_id, article_id):
	if request.method == 'POST':
		newDiscussion = Discussion(title=request.form['title'], content=request.form['content'],
								   creation_date=datetime.now(), article_id=article_id,
								   user_id=getUserID(login_session['email']),
								   user_name=login_session['username'],
								   user_picture=login_session['picture'])
		session.add(newDiscussion)
		session.commit()
		return redirect(url_for('article_discussion', category_id=category_id, subcategory_id=subcategory_id,
								article_id=article_id))
	else:
		discussions = session.query(Discussion).filter_by(article_id=article_id).all()
		if 'user_id' in login_session:
			user = getUserInfo(login_session['user_id'])
			return render_template('chapter_discussions_list.html', category_id=category_id, subcategory_id=subcategory_id,
								   article_id=article_id, discussions=discussions, user=user)
		return render_template('chapter_discussions_list.html', category_id=category_id, subcategory_id=subcategory_id,
							   article_id=article_id, discussions=discussions)


@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/<int:discussion_id>', methods=['GET','POST'])
def main_discussion(category_id, subcategory_id, article_id, discussion_id):
	if request.method == 'POST':
		newDiscussionMessage = DiscussionMessage(content=request.form['content'], date=datetime.now(),
												 discussion_id=discussion_id, user_id=getUserID(login_session['email']),
												 user_name=login_session['username'],
												 user_picture=login_session['picture'])
		session.add(newDiscussionMessage)
		session.commit()
		return redirect(
			url_for('main_discussion', category_id=category_id, subcategory_id=subcategory_id, article_id=article_id,
					discussion_id=discussion_id))
	else:
		discussion = session.query(Discussion).filter_by(id=discussion_id).one()
		messages = session.query(DiscussionMessage).filter_by(discussion_id=discussion_id).all()
		if 'user_id' in login_session:
			user = getUserInfo(login_session['user_id'])
			return render_template('main_discussion.html', category_id=category_id, subcategory_id=subcategory_id,
								   article_id=article_id, discussion_id=discussion_id, discussion=discussion,
								   messages=messages, user=user)
		return render_template('main_discussion.html', category_id=category_id, subcategory_id=subcategory_id,
							   article_id=article_id, discussion_id=discussion_id, discussion=discussion,
							   messages=messages)


@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/exercices')
def article_exercice(category_id, subcategory_id, article_id):
	exercices = session.query(ChapterExercice).filter_by(article_id=article_id).all()
	if 'user_id' in login_session:
		user = getUserInfo(login_session['user_id'])
		return render_template('chapter_exercices_list.html', category_id=category_id, subcategory_id=subcategory_id,
							   article_id=article_id, exercices=exercices, user=user)
	return render_template('chapter_exercices_list.html', category_id=category_id, subcategory_id=subcategory_id,
						   article_id=article_id, exercices=exercices)


@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/exercices/<int:exercice_id>')
def main_exercice(category_id, subcategory_id, article_id, exercice_id):
	exercice = session.query(ChapterExercice).filter_by(id=exercice_id).one()
	if 'user_id' in login_session:
		user = getUserInfo(login_session['user_id'])
		return render_template('main_exercice.html', category_id=category_id, subcategory_id=subcategory_id,
							   article_id=article_id, exercice_id=exercice_id, exercice=exercice, user=user)
	return render_template('main_exercice.html', category_id=category_id, subcategory_id=subcategory_id,
						   article_id=article_id, exercice_id=exercice_id, exercice=exercice)


@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/historic')
def article_historic(category_id, subcategory_id, article_id):
	histories = session.query(ChapterHistoric).filter_by(article_id=article_id).all()
	if 'user_id' in login_session:
		user = getUserInfo(login_session['user_id'])
		return render_template('chapter_historic.html', category_id=category_id, subcategory_id=subcategory_id,
							   article_id=article_id, histories=histories, user=user)
	return render_template('chapter_historic.html', category_id=category_id, subcategory_id=subcategory_id,
						   article_id=article_id, histories=histories)


# From here every pages need login

@app.route('/<int:category_id>/<int:subcategory_id>/new', methods=['GET','POST'])
def new_article(category_id, subcategory_id):
	if request.method == 'POST':
		newArticle = Chapter(name=request.form['name'], content=request.form['content'], creation_date=datetime.now(),
							 last_update=datetime.now(), subcategory_id=subcategory_id,
							 user_id=login_session['user_id'], user_name=login_session['username'],
							 user_picture=login_session['picture'])
		session.add(newArticle)
		session.commit()
		createHistory(" created the Chapter ", newArticle.id)
		return redirect(url_for('subcategory_menu', category_id=category_id, subcategory_id=subcategory_id))
	else:
		user = getUserInfo(login_session['user_id'])
		return render_template('new_article.html', category_id=category_id, subcategory_id=subcategory_id, user=user)


@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/exercices/new', methods=['GET','POST'])
def new_exercice(category_id, subcategory_id, article_id):
	if request.method == 'POST':
		newExercice = ChapterExercice(title=request.form['name'], content=request.form['content'],
									  answer=request.form['answer'], article_id=article_id,
									  user_id=getUserID(login_session['email']), user_name=login_session['username'],
									  user_picture=login_session['picture'])
		session.add(newExercice)
		session.commit()
		createHistory(" created the exercice ", article_id)
		return redirect(
			url_for('article_exercice', category_id=category_id, subcategory_id=subcategory_id, article_id=article_id))
	else:
		if 'user_id' in login_session:
			user = getUserInfo(login_session['user_id'])
			return render_template('new_exercice.html', category_id=category_id, subcategory_id=subcategory_id,
								   article_id=article_id, user=user)
		return redirect(url_for('showLogin'))


@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/useredit', methods=['GET','POST'])
def article_user_edit(category_id, subcategory_id, article_id):
	chapter = session.query(Chapter).filter_by(id=article_id).one()
	if request.method == 'POST':
		newPersonalArticle = PersonalChapter(name=chapter.name, content=request.form['content'],
											 creation_date=chapter.creation_date, last_update=datetime.now(),
											 article_id=article_id,
											 user_id=login_session['user_id'])
		session.add(newPersonalArticle)
		session.commit()
	
		return redirect(
			url_for('article_main', category_id=category_id, subcategory_id=subcategory_id, article_id=article_id))
	else:
		if 'user_id' in login_session:
			user = getUserInfo(login_session['user_id'])
			html = "<p> Hey </p>"
			return render_template('edit_chapter_user.html', category_id=category_id, subcategory_id=subcategory_id,
								   article_id=article_id, user=user, chapter=chapter, html=html)
		return redirect(url_for('showLogin'))
	

@app.route('/<int:category_id>/<int:subcategory_id>/<int:article_id>/generaledit', methods=['GET','POST'])
def article_general_edit(category_id, subcategory_id, article_id):
	chapter = session.query(Chapter).filter_by(id=article_id).one()
	if request.method == 'POST':
		chapter.content = request.form['content']
		createHistory(" edit ", article_id)
		return redirect(
			url_for('article_main', category_id=category_id, subcategory_id=subcategory_id, article_id=article_id))
	else:
		if 'user_id' in login_session:
			user = getUserInfo(login_session['user_id'])
			return render_template('edit_chapter_general.html', category_id=category_id, subcategory_id=subcategory_id,
								   article_id=article_id, user=user, chapter=chapter)
		return redirect(url_for('showLogin'))
	

@app.route('/<int:user_id>/myaccount')
def user_account(user_id):
	if 'user_id' in login_session:
		user = getUserInfo(login_session['user_id'])
		return render_template('user_account.html', user_id=user_id, user=user)
	return redirect(url_for('showLogin'))
	

@app.route('/<int:user_id>/mylist')
def user_myList(user_id):
	if 'user_id' in login_session:
		user = getUserInfo(login_session['user_id'])
		chapters = session.query(PersonalChapter).filter_by(user_id=login_session['user_id']).all()
		return render_template('user_myList.html', userId=user_id, user=user, chapters=chapters)
	return redirect(url_for('showLogin'))


@app.route('/<int:user_id>/myChapter/<int:pchapter_id>')
def user_myChapter(user_id, pchapter_id):
	if 'user_id' in login_session:
		user = getUserInfo(login_session['user_id'])
		chapter = session.query(PersonalChapter).filter_by(id=pchapter_id).one()
		return render_template('user_myChapter.html', userId=user_id, user=user, chapter=chapter)
	return redirect(url_for('showLogin'))


# non-page related def
def createUser(login_session):
	newUser = User(name=login_session['username'], email=login_session['email'], isCertified=False,
				   picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id


def createHistory(description, article_id):
	history = ChapterHistoric(description=description, date=datetime.now(), article_id=article_id,
							  user_id=getUserID(login_session['email']), user_name=login_session['username'],
							  user_picture=login_session['picture'])
	session.add(history)
	session.commit()
	return
	

def getUserInfo(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user


def getUserID(email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None
	
	
@app.route('/ertrteret')
def getArticleHTML():
	hey = "<p> " + "hey" + " </p>"
	return hey


# Other definitions

@app.context_processor
def override_url_for():
	return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
	if endpoint == 'static':
		filename = values.get('filename', None)
		if filename:
			file_path = os.path.join(app.root_path,
									 endpoint, filename)
			values['q'] = int(os.stat(file_path).st_mtime)
	return url_for(endpoint, **values)


if __name__ == '__main__':
	
	session.init_app(app)
	app.config['SESSION_TYPE'] = 'filesystem'
	
	app.secret_key = 'super_secret_key'
	app.debug = True
	
	app.run()
