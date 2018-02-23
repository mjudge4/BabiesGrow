from flask import Flask, render_template, flash, request, redirect, jsonify, url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Offering, Tag, Comment, User, File
import string
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
from flask import session as login_session
import random
import json
from flask import make_response
import requests
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory

UPLOAD_FOLDER = '/static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "BabiesGrow"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


engine = create_engine('mysql://root:password@localhost/mynewdatabase')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""@app.route('/offerings/new/<int:offering_id>/', methods=['GET', 'POST'])
def upload_file(offering_id):
    if 'username' not in login_session:
        return redirect('/login')
    offering_id = session.query(Offering).filter_by(id=offering_id).one()
    if request.method == 'POST':
        newFile = File(image=request.form['image'], offering_id=offering_id, user_id=login_session['user_id'])
        session.add(newFile)
        session.commit()
        return redirect(url_for('offering'))
    else:
        return render_template('uploadfile.html')"""

@app.route('/uploads/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    else:
        render_template('uploads.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

# @reference http://https://classroom.udacity.com/courses/ud330/lessons/3967218625/concepts/39636486150923

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    # Render Login Template return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.12/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.12/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/fbdisconnect', methods=['POST'])
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out"

# Disconnect based on provider

@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have logged out.")
        return redirect(url_for('offering'))
    else:
        flash("You were not logged in")
        return redirect(url_for('offering'))

# Validate the state token
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Acquire authorisation code
    code = request.data

    try:
        # Upgrade auth code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorisation code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # Abort if there was an error in access token info
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Confirm access token is for the correct user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("User ID does not match Token ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Confirm the access token is correct for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token ID does not match to application"), 401)
        print "Token ID does not match to application"
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if the user is already logged in
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already logged in'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store access token in the session
    login_session['provider'] = 'google'
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get the user's info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # Store user data to  create a response
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Disconnect by revoking user's access token

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect connected user
    access_token = login_session.get('access_token')

    if access_token is None:
        response = make_response(json.dumps('Current User is not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Enact HTTP GET request to revoke current token

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user session
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('User disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    else:
        # If for some reason the token is invalid
        response = make_response(json.dumps('Token revoke for current user failed'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUsers(user_id):
    user = session.query(User).filter_by(id=user_id).all()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/')
@app.route('/offerings/')
def offering():
    offerings = session.query(Offering).all()

    return render_template('offerings.html', offerings=offerings)

@app.route('/offerings/JSON')
def offeringJSON():
    offerings = session.query(Offering).all()
    return jsonify(offerings=[i.serialize for i in offerings])



@app.route('/offerings/<int:offering_id>/')
def offeringDetail(offering_id):
    offering = session.query(Offering).filter_by(id=offering_id).one()
    owner = getUserInfo(offering.user_id)
    tags = session.query(Tag).filter_by(offering_id=offering_id).all()
    comments = session.query(Comment).filter_by(offering_id=offering_id).all()
    commenter = getUsers(Comment.user_id)
    if 'username' not in login_session or owner.id != login_session['user_id']:
        return render_template('publicOfferingDetail.html', offering=offering, tags=tags, comments=comments, offering_id=offering_id, owner=owner, commenter=commenter)
    else:
        return render_template('offeringDetail.html', offering=offering, tags=tags,
                           comments=comments, offering_id=offering_id, owner=owner, commenter=commenter)



@app.route('/offerings/<int:offering_id>/JSON')
def offeringDetailJSON(offering_id):
    offering = session.query(Offering).filter_by(id=offering_id).one()
    tags = session.query(Tag).filter_by(offering_id=offering_id).all()
    comments = session.query(Comment).filter_by(offering_id=offering_id).all()
    return jsonify(offering=offering.serialize, Tags=[i.serialize for i in tags], Comment=[j.serialize for j in comments])


@app.route('/offerings/new/', methods=['GET', 'POST'])
def newOffering():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newOffering = Offering(title=request.form['title'], date=request.form['date'], user_id=login_session['user_id'])
        session.add(newOffering)
        session.commit()
        flash("New Offering added")
        return redirect(url_for('upload_file', offering_id=newOffering.id))
    else:
        return render_template('newoffering.html')



@app.route('/offerings/<int:offering_id>/', methods=['GET', 'POST'])
def newComment(offering_id):
    if 'username' not in login_session:
        return redirect('/login')
    offering = session.query(Offering).filter_by(id=offering_id).one()
    if request.method == 'POST':
        newComment = Comment(body=request.form['body'], offering_id=offering.id, user_id=login_session['user_id'])
        session.add(newComment)
        flash('Comment Added')
        session.commit()
        return redirect(url_for('offeringDetail', offering_id=offering_id))


@app.route('/offerings/<int:offering_id>/edit/', methods=['GET', 'POST'])
def editOffering(offering_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedOffering = session.query(Offering).filter_by(id=offering_id).one()
    if request.method == 'POST':
        if request.form['title']:
            editedOffering.title = request.form['title']
            flash("Offering updated")
            return redirect(url_for('offering'))
    else:
        return render_template('editoffering.html', offering=editedOffering)

@app.route('/offerings/<int:offering_id>/delete/', methods=['GET', 'POST'])
def deleteOffering(offering_id):
    if 'username' not in login_session:
        return redirect('/login')
    offeringToDelete = session.query(Offering).filter_by(id=offering_id).one()
    if offeringToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this offering.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(offeringToDelete)
        session.commit()
        flash("Offering deleted")
        return redirect(url_for('offering', offering_id=offering_id))
    else:
        return render_template('deleteoffering.html', offering = offeringToDelete)





if __name__ == '__main__':
    app.secret_key = 'super_duper'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
