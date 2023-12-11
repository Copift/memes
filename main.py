import base64
import hashlib
import json
import uuid

from datetime import datetime, timedelta
import mysql.connector

cnx = mysql.connector.connect(user='adm', password='1qaz@WSX12',
                              host='10.8.0.1',
                              database='memes')
cursor = cnx.cursor()


from flask import Flask, redirect, url_for, request
app = Flask(__name__)

@app.route('/auth',methods = ['GET'])
def auth():

   """authorization users with login and password GET

   a
     login : str
     password : str

   :return
        uuid - str (unicue token for session for 1 day)

   """

   try:
      login = request.args.get('login')

   except Exception as err:
         return {'requestErr: parameter login not specified'}
   try:
     passwd = request.args.get('password')
   except Exception as err:
      return {'requestErr: parameter password not specified'}
   print(f"{passwd} --  {login}")
   passwdSha = hashlib.sha256(base64.b64encode(passwd.encode('utf8'))).hexdigest()
   query = (f"SELECT user_id,user_passwd,ban_end FROM memes.users where user_login='{login}'")
   cursor.execute(query)

   anws=[]
   for row in cursor:
       anws.append(row)
   user_id=row[0]
   passwdShaDb=row[1]
   ban=row[2]
   cnx.commit()
   if ban != None:
       return "user is banned"
   elif passwdShaDb != passwdSha:
       return "password not correct"
   else:
       random_uuid = uuid.uuid4()
       current_dateTime = datetime.now()+ timedelta(days=+1)
       current_dateTime=current_dateTime.strftime("%Y-%m-%d %H:%M:%S")
       query = (f"INSERT INTO memes.tokens (token,user_id,expired_at) VALUES ('{random_uuid}','{user_id}','{current_dateTime}');")
       cursor.execute(query)
       cnx.commit()
       return {"uuid": random_uuid}

if __name__ == '__main__':
   app.run()