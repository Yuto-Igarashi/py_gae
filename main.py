import datetime
from flask import Flask, render_template,request,redirect,url_for
from google.cloud import datastore
from google.auth.transport import requests
import google.oauth2.id_token

app = Flask(__name__)

datastore_client = datastore.Client()
firebase_request_adapter = requests.Request()

def store_time(email,dt):
    entity = datastore.Entity(key=datastore_client.key('User',email,'visit'))
    entity.update({'timestamp':dt})
    datastore_client.put(entity)

def fetch_times(email,limit):
    ancestor = datastore_client.key('User',email)
    query = datastore_client.query(kind='visit',ancestor=ancestor)
    query.order = ['-timestamp']
    times = query.fetch(limit = limit)
    return times

def get_user_memo(user_id):
    query = datastore_client.query(kind='user_memo')
    query.add_filter('user_id', '=',user_id)
    user_memo = query.fetch()
    return user_memo

def cookies_id_token():
    return request.cookies.get("token")

def google_oauth_taken(id_token_arg):
    return google.oauth2.id_token.verify_firebase_token(
                id_token_arg,firebase_request_adapter
            )

def book():
    book_key = datastore_client.key('Book','Book_2')
    query = datastore_client.query(kind='Book')
    query.add_filter('title', '=', 'xyz')
    times = query.fetch()
    return times

@app.route('/')
def home():
    id_token = cookies_id_token()
    error_message = None
    claims = None
    times = None
    user_memo = None
    if id_token:
        try:
            claims = google_oauth_taken(id_token)
            user_memo=get_user_memo(claims['user_id'])
            store_time(claims['email'],datetime.datetime.now())
            times = fetch_times(claims['email'],10)
        except ValueError as exc:
            error_message = str(exc)
        #user_memoはいらない気がする?
    return render_template('index.html',user_data=claims,error_message=error_message,times = times,user_memo=user_memo)

@app.route('/book',methods=["post","get"])
def bookhttp():
    return render_template("book.html",book=book())

@app.route('/test',methods=["post","get"])
def test():
    user_id='4g3g434rg44g3gbth4g'
    query = datastore_client.query(kind='user_memo')
    query.add_filter('user_id', '=',user_id)
    user_memo = query.fetch()
    text= 'igarahis'
    if request.method=='GET':
        msg = "これはGETです"
    elif request.method =='POST':
        msg = "これはPOSTです"
    return render_template("test.html",msg=msg,user_id=user_id,user_memo=user_memo)

@app.route("/add_memo",methods=["post"])
def add_memo():
    memo_text  = request.form['memo_text']
    user_id = request.form['user_id']
    entity = datastore.Entity(key=datastore_client.key('user_memo'))
    entity.update({
        'memo_text': memo_text,
        'user_id':user_id,
        'timestamp': datetime.datetime.now()
    })
    datastore_client.put(entity)
    #homeに移動する。
    return redirect(url_for('home'))
   
if __name__ == '__main__':
    app.run(host='127.0.0.1',port=8080,debug=True)
