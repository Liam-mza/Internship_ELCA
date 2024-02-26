# Importing Libraries.. 
from flask import Flask, render_template, request, flash, Response
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField 
from wtforms import DecimalField, RadioField, SelectField, TextAreaField, FileField 
from wtforms.validators import InputRequired 
from werkzeug.security import generate_password_hash 
import psycopg
import requests as rq
import json
from keycloak import KeycloakOpenID
from flask_oidc import OpenIDConnect

from JsonProducer import UpdateOpa
from populateDB import populate_data

app = Flask(__name__) 
app.config.update({
    'SECRET_KEY': 'secretkey',
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': r"C:\Users\moul\Desktop\Kafka_with_Keycloak\app\templates\auth.json",
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'demo',
    'OIDC_TOKEN_TYPE_HINT': 'access_token',
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
})

oidc = OpenIDConnect(app)

Connected_User = None


keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/auth/",
                                 client_id="flask-client",
                                 realm_name="demo",
                                 client_secret_key="flask-client-secret")

###############################################################################
###############################################################################

# THE DIFFERENT ROUTES OF THE APP

###############################################################################
###############################################################################


# HOME PAGE
@app.route('/', methods=['GET']) 
def home(): 
    username=None
    if(oidc.user_loggedin):
        info = oidc.user_getinfo(['preferred_username', 'email'])
        username = info.get('preferred_username')
        flash(f'Succesfully logged in!')
    return render_template('index.html', login=oidc.user_loggedin,name=username) 
    

@app.route('/login', methods=['GET']) 
@oidc.require_login
def login(): 
    username=None
    if(oidc.user_loggedin):
        info = oidc.user_getinfo(['preferred_username', 'email'])
        username = info.get('preferred_username')
    return render_template('index.html', login=oidc.user_loggedin,name=username) 

@app.route('/logout')
@oidc.require_login
def logout():
     """Performs local logout by removing the session cookie."""
     refreshTok = oidc.get_refresh_token()
     oidc.logout()
     if refreshTok is not None:
        keycloak_openid.logout(refreshTok)
     oidc.logout()
     Response.delete_cookie("session")
     return home()

# PUSH DATA TO OPA
@app.route('/opaUpdate', methods=['GET']) 
def OpaUpdate():
    UpdateOpa()
    return home()


# LOAD SOME TEST DATA
@app.route('/testData', methods=['GET']) 
def testData(): 
    populate_data()
    return home() 


# CREATE A TOPIC
@app.route('/createTopic', methods=['GET', 'POST']) 
@oidc.require_login
def createTopic(): 
    form = CreateForm() 
    if form.validate_on_submit(): 
        client_id = oidc.user_getinfo(['preferred_username', 'email']).get('preferred_username') 
        topic_id = form.topic_id.data 
        description = form.Description.data
        pushNewtopic(client_id,topic_id,description)
    return render_template('createTopic.html', form=form) 


# SUBSCRIBE A CLIENT TO A TOPIC
@app.route('/newSub', methods=['GET', 'POST']) 
@oidc.require_login
def index(): 
    form = SubForm() 
    if form.validate_on_submit(): 
        client_id = form.client_id.data 
        topic_id = form.topic_id.data 
        role = form.role.data
        if(checkIfAdmin(oidc.user_getinfo(['preferred_username', 'email']).get('preferred_username'),topic_id)):
            pushSub(client_id,topic_id,role)
            flash(f'Succesfully added user: {client_id} to topic: {topic_id} with role: {role}')
            return render_template('newSub.html', form=form) 
        flash("You are not admin of this topic")
    return render_template('newSub.html', form=form) 


# LIST ALL TOPICS ON THE PLATFORM
@app.route('/list', methods=['GET', 'POST']) 
def listTopic(): 
    list = getTopics()
    return render_template('list.html', topics=list) 


# LIST ALL SUBSCRIPTIONS FOR THE GIVEN TOPIC
@app.route('/member', methods=['GET', 'POST']) 
@oidc.require_login
def listMembers(): 
    form = MemberForm() 
    if form.validate_on_submit():
        topic_id = form.topic_id.data 
        list = getMembers(topic_id)
        return render_template('member-result.html', users=list, thisTopic=topic_id) 
    return render_template('member.html', form=form) 

# LIST ALL SUBSCRIPTIONS FOR THE LOGGED USER
@app.route('/MySub', methods=['GET']) 
@oidc.require_login
def MySub():  
    username = oidc.user_getinfo(['preferred_username', 'email']).get('preferred_username')
    list = getMyTopics()
    return render_template('MySub.html', topics=list, thisUser=username)

###############################################################################
###############################################################################

# ALL THE FORMS USED BY THE APP

###############################################################################
###############################################################################
  
class ExampleForm(FlaskForm): 
    name = StringField('Name', validators=[InputRequired()]) 
    password = PasswordField('Password', validators=[InputRequired()]) 
    remember_me = BooleanField('Remember me') 
    salary = DecimalField('Salary', validators=[InputRequired()]) 
    gender = RadioField('Gender', choices=[ 
                        ('male', 'Male'), ('female', 'Female')]) 
    country = SelectField('Country', choices=[('IN', 'India'), ('US', 'United States'), 
                                              ('UK', 'United Kingdom')]) 
    message = TextAreaField('Message', validators=[InputRequired()]) 
    photo = FileField('Photo') 


class CreateForm(FlaskForm): 
    topic_id = StringField('topic_id', validators=[InputRequired()])
    Description = TextAreaField('Description', validators=[InputRequired()])

class SubForm(FlaskForm): 
    client_id = StringField('client_id', validators=[InputRequired()]) 
    topic_id = StringField('topic_id', validators=[InputRequired()])
    role = SelectField('role', choices=[('producer', 'producer'), ('consumer', 'consumer'), 
                                              ('admin', 'admin')])
    
class MemberForm(FlaskForm): 
    topic_id = StringField('topic_id', validators=[InputRequired()])


###############################################################################
###############################################################################

# HELPER FUNCTIONS FOR THE APP

###############################################################################
###############################################################################

def pushNewtopic(owner,topic,description):
    """ Push the new subscription to the db"""
    conn = None
    try:
        # Connection to the database
        conn = psycopg.connect("host=localhost port=5050 dbname=blueCity user=admin password=admin" )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("INSERT INTO subscriptions (user_id, topic_id, Role) VALUES (%s,%s,%s);",(owner,topic,"admin"))
        print("State of the DB after insert:")
        cur.execute("INSERT INTO topics (topic_id, owner, description) VALUES (%s,%s,%s);",(topic,owner,description))
 
    except (Exception, psycopg.DatabaseError) as error:
        print("Error while creating the subscription table:")
        print(error)

    finally:
        if conn is not None:
            conn.close()


def pushSub(client,topic,role):
    """ Push the new subscription to the db"""
    conn = None
    try:
        # Connection to the database
        conn = psycopg.connect("host=localhost port=5050 dbname=blueCity user=admin password=admin" )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("INSERT INTO subscriptions (user_id, topic_id, Role) VALUES (%s,%s,%s);",(client,topic,role))
        print("State of the DB after insert:")
 
    except (Exception, psycopg.DatabaseError) as error:
        print("Error while creating the subscription table:")
        print(error)

    finally:
        if conn is not None:
            conn.close()

def getTopics():
    """ Get the list of topics"""
    conn = None
    try:
        # Connection to the database
        conn = psycopg.connect("host=localhost port=5050 dbname=blueCity user=admin password=admin" )
        cur = conn.cursor()
        # Retreive the list of all topics in the dataBase 
        cur.execute("SELECT * FROM topics")
        row = cur.fetchone()
        topic_list= []
        while row is not None:
            topic_list.append(row)
            row = cur.fetchone()
 
    except (Exception, psycopg.DatabaseError) as error:
        print("Error while getting the topics:")
        print(error)

    finally:
        if conn is not None:
            conn.close()
        return topic_list

def getMyTopics():
    """Get the list of topics where the user is subscribed"""
    conn = None
    topic_list= []
    try:
        if(oidc.user_loggedin):
            info = oidc.user_getinfo(['preferred_username', 'email'])
            username = info.get('preferred_username')
            # Connection to the database
            conn = psycopg.connect("host=localhost port=5050 dbname=blueCity user=admin password=admin" )
            cur = conn.cursor()
            # Retreive the list of all topics in the dataBase 
            cur.execute("SELECT DISTINCT (topic_id, role) FROM subscriptions WHERE user_id= %s",(username,))
            row = cur.fetchone()
            while row is not None:
                topic_list.append(row[0])
                row = cur.fetchone()
 
    except (Exception, psycopg.DatabaseError) as error:
        print("Error while getting the topics:")
        print(error)

    finally:
        if conn is not None:
            conn.close()
        return topic_list
    
def getMembers(topic):
    """ Get the list of user subscibed to the given topic"""
    conn = None
    topic_list= []
    try:
        # Connection to the database
        conn = psycopg.connect("host=localhost port=5050 dbname=blueCity user=admin password=admin" )
        cur = conn.cursor()
        # Retreive the list of all topics in the dataBase 
        cur.execute("SELECT DISTINCT (user_id, role) FROM subscriptions WHERE topic_id= %s",(topic,))
        row = cur.fetchone()
        while row is not None:
            topic_list.append(row[0])
            row = cur.fetchone()
 
    except (Exception, psycopg.DatabaseError) as error:
        print("Error while getting the topics:")
        print(error)

    finally:
        if conn is not None:
            conn.close()
        return topic_list
    

def checkIfAdmin(user,topic):
    jsonTemplate= {"input":{"name": user,"topic": topic}}

    try:
        url = "http://localhost:8181/v1/data/app/authz/is_admin"
        response = rq.post(url, data=json.dumps(jsonTemplate, indent=2))
        result = response.json().get("result")
        if result == None:
            return False
        return(result)
    
    except Exception as error:
        print("Error while sending data to OPA")
        print("MAKE SURE THAT YOU LAUNCHED THE KUBECTL PORT FORWARDING FOR OPA WITH: kubectl port-forward svc/opa 8181:8181 ")
        print("Error message: ")
        print(error)
        return False


if __name__ == '__main__': 
    app.run() 