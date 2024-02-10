server = 'copift.ru'
port = '5000'
bdUser='adm'
bdPasswd='1qaz@WSX12'
bdName='memes'

import base64
import hashlib
import io
import logging
import os
import uuid
from collections import Counter
from datetime import datetime, timedelta

import mysql.connector
from PIL import Image
from flask import Flask, make_response, send_file
from flask import has_request_context, request
from flask.logging import default_handler
from flask_cors import CORS, cross_origin
from flask_json import FlaskJSON, as_json



class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)


formatter = RequestFormatter(
    '[%(asctime)s] %(remote_addr)s requested %(url)s  %(levelname)s : %(message)s'
)
default_handler.setFormatter(formatter)
app = Flask(__name__)
# mysql = MySQL()# MySQL configurations
# app.config["MYSQL_DATABASE_USER"] = "adm"
# app.config["MYSQL_DATABASE_PASSWORD"] = "1qaz@WSX12"
# app.config["MYSQL_DATABASE_DB"] = "memes"
# app.config["MYSQL_DATABASE_HOST"] = "10.8.0.1"
# mysql.init_app(app)
#
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))

# cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
#                                host='localhost',
#                               database=bdName)
# cursor = cnx.cursor()



# def checkConnect(cnx=cnx):
#
#     if not(cnx.is_connected()):
#         cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
#                                        host='localhost',
#                                       database=bdName)
#         cursor = cnx.cursor()
#

def createResponse(text: dict, code: int):
    res = make_response(str(text), code)
    res.headers['Content-Type'] = 'application/json'
    return res


def checkUuid(uuid2):
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    cursor.execute(
        f'select token  from memes.tokens where expired_at > "{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")}"')
    fl = False
    for row in cursor:

        try:
            if row[0] == uuid2:
                fl = True
                cnx.commit()
                break
        except Exception as err:
            print(err)
    if fl:
        return True
    else:
        return False


def getMaxUser():
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    cursor.execute("SELECT MAX(user_id) FROM users ;")
    for max in cursor:
        return max[0]


def getMaxPost():
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    cursor.execute("SELECT MAX(post_id) FROM posts ;")
    for max in cursor:
        return max[0]


# +
@app.route('/uploadPost', methods=['POST'])
@cross_origin()
@as_json
def addPost():
    """add post to user via POST
       :args
        uuid : str
        files : img optional
        text : str optional
      :return
          status : str
          post_id : int
      :raise
         401(not auth):
           'err':'not auth,uuid dont active'
         400(bad request):
             'err_code':1 -parameters  not found
             'err_code':100 - SQL error
      """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid']
    paramsReq = list(request.form.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    uuid = request.form['uuid']
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    img_data = None
    text = None
    if 'files' in request.files:
        file = request.files['files']
        img = Image.open(file.stream)
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_data = img_buffer.getvalue()
    if 'text' in request.form:
        text = request.form['text']
    try:
        current_dateTime = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"SELECT user_id FROM tokens WHERE token = '{uuid}'")
        for row in cursor:
            user_id = row[0]
        cnx.commit()
        cursor.execute(
            f"INSERT INTO memes.posts (created_at, source, DateText, user_id, is_deleted_admin) VALUES (%s,%s,%s,%s,%s);",
            (current_dateTime, img_data, text, user_id, 0))

        cnx.commit()
        cursor.execute(
            f"SELECT MAX(post_id)\
        FROM posts p ;")
        for max in cursor:
            post_id = max[0]
        response = {'status': 'insert succsesful', 'post_id': post_id}
        app.logger.error(str(response))
        return response, 200
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400


# +
@app.route('/editPost', methods=['POST'])
@cross_origin()
@as_json
def editPost():
    """edit post of user  via POST
          :args
           uuid : str
           files : img optional
           text : str optional
           post_id : int
         :return
             status : str
             post_id : int
         :raise
            401(not auth):
              'err':'not auth,uuid dont active'
            400(bad request):
               'err_code':1 -parameters  not found
               'err_code':2 - The post does not exist
               'err_code':100 - SQL error
         """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    print(request.args)
    print(request.values)
    params = ['uuid', 'post_id']
    paramsReq = list(request.form.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    uuid = request.form['uuid']
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    post_id = request.form['post_id']
    if int(post_id) > getMaxPost() or str(post_id) == '':
        response = {'err_code': 2, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    if 'files' in request.files:
        file = request.files['files']
        img = Image.open(file.stream)
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_data = img_buffer.getvalue()

        try:
            cursor.execute(
                f"UPDATE  memes.posts SET  source = %s  where post_id= %s", (img_data, int(post_id)))
            cnx.commit()
        except Exception as err:
            response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
            app.logger.error(str(response))
            return response, 400

    if 'text' in request.form:
        text = request.form['text']
        try:
            cursor.execute(
                f"UPDATE  memes.posts SET  DateText = %s  where post_id= %s", (text, int(post_id)))
            cnx.commit()
        except Exception as err:
            response = {'err_code': 1, 'err': f'SQL err: {err}'}  #
            app.logger.error(str(response))
            return response, 400
    app.logger.error(str({'status': 'update succsesful', 'post_id': post_id}))
    return {'status': 'update succsesful', 'post_id': post_id}, 200





# +
@app.route('/editUser', methods=['POST'])
@cross_origin()
@as_json
def editUser():
    try:
        """edit user  via POST
              :args
               uuid : str
               user_login: str
               user_name:str
               user_surname:str
               date_of_birth; date
               files : img optional

             :return
                 status : str
                 user_id : int
             :raise
                401(not auth):
                  'err':'not auth,uuid dont active'
                400(bad request):
                   'err_code':1 -parameters  not found

                   'err_code':100 - SQL error
             """
        # params = ['uuid', 'user_login', 'user_name', 'user_surname', 'date_of_birth']
        # paramsReq = list(request.form.keys())
        # notFound = list((Counter(params) - Counter(paramsReq)).elements())
        # if len(notFound) > 0:
        #     response = {'err_code': 1,
        #                 'err': f'parameters {",".join(notFound)} not found'}
        #     app.logger.error(str(response))
        #     return response, 400

        cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                       host='localhost',
                                      database=bdName)
        cursor = cnx.cursor()

        uuid = request.form['uuid']
        # if not (checkUuid(uuid)):
        #     app.logger.error(str({'err': 'not auth,uuid dont active'}))

        user_login = request.form['user_login']
        user_name= request.form['user_name']
        user_surname = request.form['user_surname']
        date_of_birth = request.form['date_of_birth']

        if 'files' in request.files:
            file = request.files['files']
            img = Image.open(file.stream)
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG')
            img_data = img_buffer.getvalue()
            try:
                cursor.execute(
                    f"UPDATE  users SET  user_img = %s  where user_id=  user_id = (SELECT user_id FROM tokens WHERE token = %s);", (img_data, uuid))
                cnx.commit()
            except Exception as err:
                response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
                app.logger.error(str(response))
                return response, 400


        try:
            cursor.execute(
                f"UPDATE users SET  user_login = %s, \
               user_name = %s, \
               user_surname = %s,  \
               date_of_birth = %s  where user_id = (SELECT user_id FROM tokens WHERE token = %s);", (user_login,user_name,user_surname,date_of_birth,uuid))
            cnx.commit()
        except Exception as err:
            response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
            app.logger.error(str(response))
            return response, 400
        app.logger.error(str({'status': 'update succsesful'}))
        return {'status': 'update succsesful'}, 200

    except Exception as err:
        response = {'err_code': 1, 'err': f'ERRRRORRRRRR {err}'}  #
        app.logger.error(str(response))
        return response, 400

@app.route('/deletePost', methods=['GET'])
@cross_origin()
@as_json
# +
def deletePost():
    """delete post of user  via GET
             :args
              uuid : str
              post_id : int
            :return
                status : str
                post_id : int
            :raise
               401(not auth):
                 'err':'not auth,uuid dont active'
               400(bad request):
                  'err_code':1 -parameters  not found
                  'err_code':2 - The post does not exist
                  'err_code':100 - SQL error
            """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'post_id']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    post_id = request.args.get('post_id')
    if int(post_id) > getMaxPost() or str(post_id) == '':
        response = {'err_code': 2, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    try:
        cursor.execute(
            f"UPDATE posts SET is_deleted = 1  \
        WHERE post_id = '{post_id}' \
        AND user_id = (SELECT user_id FROM tokens WHERE token = '{uuid}');")
        cnx.commit()
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    app.logger.error(str({'status': 'delete succsesful', 'post_id': post_id}))
    return {'status': 'delete succsesful', 'post_id': post_id}, 200


@app.route('/returnPost', methods=['GET'])
@cross_origin()
@as_json
def returnPost():
    """return post of user  via GET
               :args
                uuid : str
                post_id : int
              :return
                  status : str
                  post_id : int
              :raise
                 401(not auth):
                   'err':'not auth,uuid dont active'
                 400(bad request):
                    'err_code':1 -parameters  not found
                    'err_code':2 - The post does not exist
                    'err_code':100 - SQL error
              """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'post_id']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    post_id = request.args.get('post_id')
    if int(post_id) > getMaxPost() or str(post_id) == '':
        response = {'err_code': 2, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    try:
        cursor.execute(
            f"UPDATE posts SET is_deleted = 0  \
          WHERE post_id = '{post_id}' \
          AND user_id = (SELECT user_id FROM tokens WHERE token = '{uuid}');")
        cnx.commit()
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    app.logger.error(str(({'status': 'return post succsesful', 'post_id': post_id}, 200)))
    return {'status': 'return post succsesful', 'post_id': post_id}, 200


# +
@app.route('/setBanPost', methods=['GET'])
@cross_origin()
@as_json
def setBanPost():
    """return post of user  via GET
               :args
                uuid : str
                post_id : int
              :return
                  status : str
                  post_id : int
              :raise
                 401(not auth):
                   'err':'not auth,uuid dont active'
                 400(bad request):
                    'err_code':1 -parameters  not found
                    'err_code':2 - The post does not exist
                    'err_code':3 - you not allowed to this action, user dont in moderators
                    'err_code':100 - SQL error
              """

    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'post_id']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    post_id = request.args.get('post_id')
    if int(post_id) > getMaxPost() or str(post_id) == '':
        response = {'err_code': 2, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    cursor.execute(f"SELECT IF(EXISTS(SELECT * FROM moderatores  \
                    WHERE user_id = (SELECT user_id FROM tokens WHERE token = '{uuid}')), 1, 0)  \
                    AS is_moderator; ")
    for row in cursor:
        is_admin = row[0]
    if is_admin == None:
        response = {'err_code': 3, 'err': 'u not allowed to this action, user dont admin'}
        app.logger.error(str(response))
        return response, 400
    try:

        cursor.execute(
            f"UPDATE posts  \
SET is_deleted_admin = 1  \
WHERE post_id = {post_id};")
        cnx.commit()

    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    app.logger.error(str(({'status': 'set ban to  post succsesful', 'post_id': post_id}, 200)))
    return {'status': 'set ban to  post succsesful', 'post_id': post_id}, 200


# +
@app.route('/downBanPost', methods=['GET'])
@cross_origin()
@as_json
def downBanPost():
    """return post from ban of user  via GET
                  :args
                   uuid : str
                   post_id : int
                 :return
                     status : str
                     post_id : int
                 :raise
                    401(not auth):
                      'err':'not auth,uuid dont active'
                    400(bad request):
                       'err_code':1 -parameters  not found
                       'err_code':2 - The post does not exist
                       'err_code':3 - you not allowed to this action, user dont in moderators
                       'err_code':100 - SQL error
                 """

    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'post_id']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}

        app.logger.error(str(response))
        return response, 400

    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    post_id = request.args.get('post_id')
    if int(post_id) > getMaxPost() or str(post_id) == '':
        response = {'err_code': 2, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    cursor.execute(f"SELECT IF(EXISTS(SELECT * FROM moderatores  \
                        WHERE user_id = (SELECT user_id FROM tokens WHERE token = '{uuid}')), 1, 0)  \
                        AS is_moderator; ")
    for row in cursor:
        is_admin = row[0]
    if is_admin == None:
        response = {'err_code': 3, 'err': 'u not allowed to this action, user dont admin'}
        app.logger.error(str(response))
        return response, 400
    try:

        cursor.execute(
            f"UPDATE posts  \
    SET is_deleted_admin = 0  \
    WHERE post_id = {post_id};")
        cnx.commit()

    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    app.logger.error(str(({'status': 'set ban to  post succsesful', 'post_id': post_id}, 200)))
    return {'status': 'set ban to  post succsesful', 'post_id': post_id}, 200


# +
@app.route('/post/<int:idPost>', methods=['GET'])
@cross_origin()
@as_json
def get_post(idPost):
    """return post data via GET
                     :args
                       uuid : str

                     :return
                         post_id : int
                         text: str
                         image_link:str
                     :raise
                        401(not auth):
                          'err':'not auth,uuid dont active'
                        400(bad request):
                           'err_code':1 -parameters  not found
                           'err_code':2 - The post does not exist
                           'err_code':3 - The post deleted by user or moderator
                           'err_code':100 - SQL error
                     """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    if int(idPost) > getMaxPost():
        response = {'err_code': 2, 'err': f'The post does not exist'}  #

        app.logger.error(str(response))
        return response, 400

    text = None
    try:
        cursor.execute(
            f"SELECT DateText FROM memes.posts where post_id='{idPost}' and is_deleted_admin=0 and is_deleted=0;")
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    for Datetext in cursor:
        text = Datetext[0]
    if text == None:
        response = {'err_code': 3, 'err': f'The post deleted by user or moderator'}  #

        app.logger.error(str(response))
        return response, 400
    response = {'post_id': idPost, 'text': text,
                "image_link": f"http://{server}:{port}/postsImages/{idPost}.jpg?uuid={uuid}", }
    app.logger.error(str(response))
    return response, 200


# +
@app.route('/auth', methods=['GET'])
@cross_origin()
@as_json
def auth():
    """authorization users with login and password  via GET request
    :args
     login : str
     password : str
   :return
        uuid : str (unique token for session for 1 day)
        is_admin: bool
   :raise
      400(bad Request):
        'err_code':1 - some parameters not found'
        'err_code':2 - given more parameters than required'
        'err_code':3 - parameter is empty'
        'err_code':4 - user is banned'
        'err_code':5 - password not correct'
        'err_code':6 - login not found'
   """

    # check parameters

    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['login', 'password']
    paramsReq = list(request.args.keys())
    print(paramsReq)
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400
    if not (len(params) == len(paramsReq)):
        response = {'err_code': 2,
                    'err': f'given more parameters than reqired'}
        app.logger.error(str(response))
        return response, 400
    for item in request.args.items():
        if len(str(item[1])) == 0:
            response = {'err_code': 3,
                        'err': f'parameter {item[0]} is empty'}
            app.logger.error(str(response))
            return response, 400

    login = request.args.get('login')
    passwd = request.args.get('password')

    passwdSha = hashlib.sha256(base64.b64encode(passwd.encode('utf8'))).hexdigest()
    cursor.execute(f"SELECT user_id,user_passwd,ban_end,l.is_admin FROM memes.users as u \
left join \
(select user_id as is_admin from moderatores m ) as l on l.is_admin = u.user_id \
WHERE u.user_login='{login}'")
    user_id = 0
    for row in cursor:
        user_id = row[0]
        passwdShaDb = row[1]
        ban = row[2]
        is_admin = row[3]
    if user_id == 0:
        response = {'err_code': 6,
                    'err': f'login not found'}
        return response, 400
    cnx.commit()
    if ban != None:

        response = {'err_code': 4,
                    'err': f'user is banned'}

        app.logger.error(str(response))
        return response, 400
    elif passwdShaDb != passwdSha:
        response = {'err_code': 5,
                    'err': f'password not correct'}
        app.logger.error(str(response))
        return response, 400
    else:
        random_uuid = uuid.uuid4()
        current_dateTime = (datetime.now() + timedelta(days=+1)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute(
                f"INSERT INTO memes.tokens (token,user_id,expired_at) VALUES ('{random_uuid}','{user_id}','{current_dateTime}');")
            cnx.commit()
        except Exception as err:
            response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
            app.logger.error(str(response))
            return response, 400
        response = {'uuid': f'{str(random_uuid)}', 'is_admin': bool(not (is_admin == None))}
        res = createResponse(response, 200)
        res.headers['Content-Type'] = 'application/json'
        app.logger.error(str(response))
        return response, 200


@app.route('/setLike', methods=['GET'])
@cross_origin()
@as_json
def setLike():
    """set Like to post via GET
     uuid : str
     post_id : str

   :return
    status: str
    post_id :int

    :raise
        401(not auth):
          'err':'not auth,uuid dont active'
        400(bad request):
           'err_code':1 -parameters  not found
           'err_code':2 - given more parameters than reqired
           'err_code':3 - parameter is empty
           'err_code':4 - The post does not exist
           'err_code':5 - The post deleted
           'err_code':100 - SQL error
   """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'post_id']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400
    if not (len(params) == len(paramsReq)):
        response = {'err_code': 2,
                    'err': f'given more parameters than reqired'}
        app.logger.error(str(response))
        return response, 400
    for item in request.args.items():
        if len(str(item[1])) == 0:
            response = {'err_code': 3,
                        'err': f'parameter {item[0]} is empty'}
            app.logger.error(str(response))
            return response, 400
    post_id = request.args.get('post_id')
    uuid = request.args.get('uuid')

    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    if int(post_id) > getMaxPost():
        response = {'err_code': 4, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400
    cursor.execute(
        f"SELECT is_deleted,is_deleted_admin from posts where post_id={post_id}")
    for is_deleted, is_deleted_admin in cursor:
        if is_deleted or is_deleted_admin:
            response = {'err_code': 5, 'err': f'The post deleted'}  #
            app.logger.error(str(response))
            return response, 400

    try:
        cursor.execute(
            f"INSERT INTO likes (post_id, user_id, is_active)  \
                VALUES ( '{post_id}',  \
                (SELECT user_id FROM tokens WHERE token = '{uuid}'), 1 );")
        cnx.commit()
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    app.logger.error(str(({'status': 'set like to  post succsesful', 'post_id': post_id}, 200)))
    return {'status': 'set like to  post succsesful', 'post_id': post_id}, 200


@app.route('/downLike', methods=['GET'])
@cross_origin()
@as_json
def downLike():
    """down Like to post via GET
         uuid : str
         post_id : str

       :return
        status: str
        post_id :int

        :raise
            401(not auth):
              'err':'not auth,uuid dont active'
            400(bad request):
               'err_code':1 -parameters  not found
               'err_code':2 - given more parameters than reqired
               'err_code':3 - parameter is empty
               'err_code':4 - The post does not exist
               'err_code':5 - The post deleted
               'err_code':100 - SQL error
       """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'post_id']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400
    if not (len(params) == len(paramsReq)):
        response = {'err_code': 2,
                    'err': f'given more parameters than reqired'}
        app.logger.error(str(response))
        return response, 400
    for item in request.args.items():
        if len(str(item[1])) == 0:
            response = {'err_code': 3,
                        'err': f'parameter {item[0]} is empty'}
            app.logger.error(str(response))
            return response, 400
    post_id = request.args.get('post_id')
    uuid = request.args.get('uuid')

    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    if int(post_id) > getMaxPost():
        response = {'err_code': 4, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400
    cursor.execute(
        f"SELECT is_deleted,is_deleted_admin from posts where post_id={post_id}")
    for is_deleted, is_deleted_admin in cursor:
        if is_deleted or is_deleted_admin:
            response = {'err_code': 5, 'err': f'The post deleted'}  #
            app.logger.error(str(response))
            return response, 400

    try:
        cursor.execute(
            f"UPDATE likes SET is_active = 0  \
WHERE post_id = '{post_id}' \
AND user_id = (SELECT user_id FROM tokens WHERE token = '{uuid}');")
        cnx.commit()
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    app.logger.error(str(({'status': 'down like to  post succsesful', 'post_id': post_id}, 200)))
    return {'status': 'down like to  post succsesful', 'post_id': post_id}, 200


@app.route('/setBan', methods=['GET'])
@cross_origin()
@as_json
def setBan():
    """set Ban to user
     uuid : str
     user_id: str
   :return
    status:str
    user_id L int
    :raise
    401(not auth):
      'err':'not auth,uuid dont active'
    400(bad request):
       'err_code':1 -parameters  not found
       'err_code':2 - The user does not exist
       'err_code':3 - you not allowed to this action, user dont in moderators
       'err_code':100 - SQL error

    """

    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'user_id']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    user_id = request.args.get('user_id')
    if int(user_id) > getMaxUser() or user_id == '':
        response = {'err_code': 2, 'err': f'The user does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    cursor.execute(f"SELECT IF(EXISTS(SELECT * FROM moderatores  \
                       WHERE user_id = (SELECT user_id FROM tokens WHERE token = '{uuid}')), 1, 0)  \
                       AS is_moderator; ")
    for row in cursor:
        is_admin = row[0]
    if is_admin == None:
        response = {'err_code': 3, 'err': 'u not allowed to this action, user dont admin'}
        app.logger.error(str(response))
        return response, 400
    try:
        current_dateTime = (datetime.now() + timedelta(days=+7)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            f"UPDATE users  \
                SET ban_end = '{current_dateTime}'  \
                WHERE user_id = {user_id};")
        cnx.commit()

    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    app.logger.error(str(({'status': 'set ban to user succsesful ', 'user_id': user_id}, 200)))
    return {'status': 'set ban to user succsesful ', 'user_id': user_id}, 200


@app.route('/getUserData', methods=['GET'])
@cross_origin()
def getUserData():
    """get user data  via login via GET
   :arg
     uuid: str
     user_login : str

   :return
        user_id : int
        user_login : str
        user_name : str
        user_surname : str
        avatar_link: str
        date_of_birth : datetime
    :raise
    401(not auth):
      'err':'not auth,uuid dont active'
    400(bad request):
       'err_code':1 -parameters  not found
       'err_code':2 - The user does not exist
       'err_code':100 - SQL error


   """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'user_login']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401
    user_login = request.args.get('user_login')
    cursor.execute(f'SELECT user_id FROM user WHERE user_login={user_login}')
    for id in cursor:
        user_id = id
    if int(user_id) > getMaxUser() or user_login == '':
        response = {'err_code': 2, 'err': f'The user does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    try:
        cursor.execute(
            f"SELECT user_id,user_login,user_name,user_surname,date_of_birth FROM memes.users where user_login='{user_login}';")
        for user_id, user_login, user_name, user_surname, date_of_birth in cursor:
            return {"user_id": user_id,
                    "user_login": user_login,
                    'avatar_link': f'http://{server}:{port}/userAvatar/{user_id}.jpg?uuid={uuid}',
                    "date_of_birth": date_of_birth,
                    "user_surname": user_surname,
                    "user_name": user_name}

    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400


@app.route('/me', methods=['GET'])
@cross_origin()
@as_json
def me():
    """get user data
   :arg
     uuid: str

   :return
        user_id : int
        user_login : str
        user_name : str
        user_surname : str
        user_img : str - link
        date_of_birth : datetime
    :raise
    401(not auth):
      'err':'not auth,uuid dont active'
    400(bad request):
       'err_code':1 -parameters  not found
   """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400
    uuid = request.args.get('uuid')

    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    try:
        cursor.execute(f"SELECT u.user_id,u.user_login, u.user_name,u.user_surname,u.date_of_birth FROM memes.users as u JOIN tokens AS t ON t.user_id = u.user_id \
                                   WHERE t.token  = '{uuid}';")
        for user_id, user_login, user_name, user_surname, date_of_birth in cursor:
            print(str(date_of_birth))
            return {"user_id": user_id, "user_login": user_login, "user_name": user_name, "user_surname": user_surname,
                    "user_img": f'http://{server}:{port}/userAvatar/{user_id}.jpg?uuid={uuid}', "date_of_birth": str(date_of_birth)}

    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400


@app.route('/postsImages/<int:pid>.jpg', methods=['GET'])
@cross_origin()
def get_image(pid):
    '''  return image of post_id = pid '''
    cnx2 = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                    host='localhost',
                                   database=bdName)
    cursor2 = cnx2.cursor()

    uuid = request.args.get('uuid')
    # if not (checkUuid(uuid)):
    #     return 'uuid dont active'

    cursor2.execute(
        f"SELECT source FROM memes.posts where post_id='{pid}';")
    for source in cursor2:

        return send_file(
            io.BytesIO(source[0]),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='%s.jpg' % pid)
    cnx2.close()


@app.route('/userAvatar/<int:pid>.jpg', methods=['GET'])
@cross_origin()
def get_avatar(pid):
    '''  return image of user avatart = pid'''
    cnx2 = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                    host='localhost',
                                   database=bdName)
    cursor2 = cnx2.cursor()
    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return 'uuid dont active'
    cursor2.execute(
        f"SELECT user_img FROM memes.users where user_id='{pid}';")
    for source in cursor2:

        return send_file(
            io.BytesIO(source[0]),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='%s.jpg' % pid)


@app.route('/addUser', methods=['POST'])
@cross_origin()
@as_json
def addUser():
    """add user via POST

    :args

     user_login: str
     user_passwd: str
     user_name: str
     user_surname: str
     date_of_birth: str
     files: img

   :return
    status:str
    :raise
      400(bad Request):
        'err_code':1 - some parameters not found'
        'err_code':2 - avatar not found.'
        'err_code':3 - parameter is empty'
        'err_code':4 - login already use'
   """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['user_login', 'user_passwd', 'user_name', 'user_surname', 'date_of_birth']
    paramsReq = list(request.form.keys())
    print(paramsReq)

    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400

    for item in request.args.items():
        if len(str(item[1])) == 0:
            response = {'err_code': 3,
                        'err': f'parameter {item[0]} is empty'}
            app.logger.error(str(response))
            return response, 400
    img_data = None
    print(request.files)
    if 'files' in request.files:
        file = request.files['files']
        img = Image.open(file.stream)
        img_buffer = io.BytesIO()
        try:
            img.save(img_buffer, format='JPEG')
        except:
            img.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()
    else:
        response = {'err_code': 2,
                    'err': f'avatar not found'}
        app.logger.error(str(response))
        return response, 400
    if img_data == None:

        img = Image.open("spitsi.png")
        img_buffer = io.BytesIO()
        try:
            img.save(img_buffer, format='JPEG')
        except:
            img.save(img_buffer, format='PNG')

    user_login = request.form.get('user_login')
    cursor.execute(
        f"SELECT user_login FROM users;")
    logins = []
    for login in cursor:
        logins.append(login[0])
    if user_login in logins:
        response = {'err_code': 4,
                    'err': f'login already use'}
        app.logger.error(str(response))
        return response, 400
    cnx.commit()

    string = request.form.get('user_passwd')
    user_passwd = hashlib.sha256(base64.b64encode(string.encode('utf8'))).hexdigest()
    user_name = request.form.get('user_name')
    user_surname = request.form.get('user_surname')
    date_of_birth = request.form.get('date_of_birth')
    try:
        cursor.execute(
            f"INSERT INTO users (user_login, user_passwd, user_name, user_surname, date_of_birth, user_img) VALUES (%s,%s,%s,%s,%s,%s);",
            (user_login, user_passwd, user_name, user_surname, date_of_birth, img_data))
        cnx.commit()
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400
    app.logger.error(str(({'status': 'add user succsesful'}, 200)))
    return {'status': 'add user succsesful'}, 200


@app.route('/getPostsGroup', methods=['GET'])
@cross_origin()
@as_json
def getPostsGroup():
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor2 = cnx.cursor()
    """get last 20 post at id
        :arg
          uuid: str
          post_id-int
          count: int - how many posts you need

        :return
        [{"post":{"Text","created_at","id","image_link","is_liked","likes"},
        "user":{"avatarLink","uuid=","user_id","user_login","user_name","user_surname"}}]

        :raises

        401(not auth):
          'err':'not auth,uuid dont active'
        400(bad request):
           'err_code':1 -parameters  not found
           'err_code':2 - given more parameters than reqired
           'err_code':3 - parameter is empty
           'err_code':4 - The post does not exist
            'err_code':100 - SQL error
        """
    params = ['uuid', 'post_id', 'count']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400
    if not (len(params) == len(paramsReq)):
        response = {'err_code': 2,
                    'err': f'given more parameters than reqired'}
        app.logger.error(str(response))
        return response, 400
    for item in request.args.items():
        if len(str(item[1])) == 0:
            response = {'err_code': 3,
                        'err': f'parameter {item[0]} is empty'}
            app.logger.error(str(response))
            return response, 400
    post_id = request.args.get('post_id')
    uuid = request.args.get('uuid')

    if not (checkUuid(uuid)):
        app.logger.error('not auth,uuid dont active')
        return {'err': 'not auth,uuid dont active'}, 401

    if int(post_id) > getMaxPost():
        response = {'err_code': 4, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    count = request.args.get('count')

    id = post_id

    try:
        cursor2.execute(f"SELECT DISTINCT p.post_id, p.created_at, p.DateText, p.user_id, u.user_login, u.user_name, u.user_surname, l.is_liked \
    FROM posts p \
    JOIN users u ON p.user_id = u.user_id \
    LEFT JOIN (SELECT post_id AS is_liked FROM likes \
    WHERE user_id = (SELECT user_id FROM tokens WHERE token = %s) AND is_active=1) \
    AS l ON p.post_id = l.is_liked \
    WHERE p.is_deleted = 0 \
    AND p.post_id <= (SELECT MAX(post_id) - %s FROM posts WHERE p.is_deleted = 0) \
    AND u.ban_end is NULL               \
    AND p.is_deleted_admin = 0 \
    ORDER BY p.post_id DESC \
    LIMIT %s;", (uuid, int(id), int(count)))

        anws = {'posts': []}
        for post_id, created_at, DateText, user_id, user_login, user_name, user_surname, is_liked in cursor2:
            anws['posts'].append({'post': {
                'id': post_id,
                'created_at': created_at,
                'Text': DateText,
                "image_link": f"http://{server}:{port}/postsImages/{post_id}.jpg?uuid={uuid}",
                'likes': 0,
                'is_liked': bool(not (is_liked == None))
            },

                'user': {
                    'user_id': user_id,
                    'user_login': user_login,
                    'user_name': user_name,
                    'user_surname': user_surname,
                    'avatarLink': f'http://{server}:{port}/userAvatar/{user_id}.jpg?uuid={uuid}'
                }
            })
        cnx.commit()
        for post in anws['posts']:
            likes = 0
            try:
                # print(post)
                id = post['post']['id']
                # print(id)
                cursor2.execute(f"SELECT COUNT(DISTINCT user_id) AS likes_count \
                                FROM likes \
                                WHERE post_id = {id} \
                                AND is_active = 1")
                for count in cursor2:
                    likes = count[0]
            except Exception as err:
                print(err, '!!!')
            post['post'].update({'likes': likes})

        app.logger.error(f'return {str(anws)}')
        return anws
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400


@app.route('/getPostsGroupUser', methods=['GET'])
@cross_origin()
@as_json
def getPostsGroupUser():
    """
    get last 20 post at id of user
     :arg
       uuid: str
       post_id-int
       count: int - how many posts you need

     :return
     [{"post":{"Text","created_at","id","image_link","is_liked","likes"},
     "user":{"avatarLink","uuid=","user_id","user_login","user_name","user_surname"}}]

     :raises

     401(not auth):
       'err':'not auth,uuid dont active'
     400(bad request):
        'err_code':1 -parameters  not found
        'err_code':2 - given more parameters than reqired
        'err_code':3 - parameter is empty
        'err_code':4 - The post does not exist
         'err_code':100 - SQL error
     """
    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor2 = cnx.cursor()
    params = ['uuid', 'post_id', 'count']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400
    if not (len(params) == len(paramsReq)):
        response = {'err_code': 2,
                    'err': f'given more parameters than reqired'}
        app.logger.error(str(response))
        return response, 400
    for item in request.args.items():
        if len(str(item[1])) == 0:
            response = {'err_code': 3,
                        'err': f'parameter {item[0]} is empty'}
            app.logger.error(str(response))
            return response, 400
    post_id = request.args.get('post_id')
    uuid = request.args.get('uuid')

    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    if int(post_id) > getMaxPost():
        response = {'err_code': 4, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    count = request.args.get('count')

    id = post_id
    try:
        cursor2.execute(f"SELECT DISTINCT p.post_id, p.created_at, p.DateText, p.user_id, u.user_login, u.user_name, u.user_surname, l.is_liked \
    FROM posts p \
    JOIN users u ON p.user_id = u.user_id \
    JOIN tokens AS t ON t.user_id = p.user_id  \
    LEFT JOIN (SELECT post_id AS is_liked FROM likes \
    WHERE user_id = (SELECT user_id FROM tokens WHERE token = %s) AND is_active=1) \
    AS l ON p.post_id = l.is_liked \
    WHERE p.is_deleted = 0 \
           and t.token = %s \
           and p.is_deleted_admin=0 \
            AND p.post_id <= (SELECT MAX(post_id) - %s FROM posts WHERE p.is_deleted = 0) \
    ORDER BY p.post_id DESC \
    LIMIT %s;", (uuid, uuid, int(id), int(count)))
        #            #   and  p.user_id = (SELECT user_id FROM tokens WHERE token = %s)\
        # cursor.execute(f"SELECT p.post_id, p.created_at, p.DateText, p.user_id, u.user_login, u.user_name, u.user_surname \
        #     FROM posts p \
        #     JOIN users u ON p.user_id = u.user_id \
        #     JOIN tokens AS t ON t.user_id = u.user_id \
        #                            WHERE t.token  = '{uuid}' \
        #      AND p.is_deleted = 0 \
        #     AND p.post_id <= (SELECT MAX(post_id) - '{id}' FROM posts WHERE is_deleted = 0) \
        #     ORDER BY p.post_id DESC \
        #     LIMIT {count};")
        anws = {'posts': []}
        for post_id, created_at, DateText, user_id, user_login, user_name, user_surname, is_liked in cursor2:
            anws['posts'].append({'post': {
                'id': post_id,
                'created_at': created_at,
                'Text': DateText,
                "image_link": f"http://{server}:{port}/postsImages/{post_id}.jpg?uuid={uuid}",
                'likes': 0,
                'is_liked': bool(not (is_liked == None))
            },

                'user': {
                    'user_id': user_id,
                    'user_login': user_login,
                    'user_name': user_name,
                    'user_surname': user_surname,
                    'avatarLink': f'http://{server}:{port}/userAvatar/{user_id}.jpg?uuid={uuid}'
                }
            })
        cnx.commit()
        for post in anws['posts']:
            likes = 0
            try:
                print(post)
                id = post['post']['id']
                print(id)
                cursor2.execute(f"SELECT COUNT(DISTINCT user_id) AS likes_count \
                                             FROM likes \
                                             WHERE post_id = {id} \
                                             AND is_active = 1")
                for count in cursor2:
                    likes = count[0]
            except Exception as err:
                print(err, '!!!')
            post['post'].update({'likes': likes})
        app.logger.error(f'return {str(anws)}')
        return anws
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400


@app.route('/getDeletedPostsGroupUser', methods=['GET'])
@cross_origin()
def getDeletedPostsGroupUser():
    """
    get last deleted 20 post at id of user
     :arg
       uuid: str
       post_id-int
       count: int - how many posts you need

     :return
     [{"post":{"Text","created_at","id","image_link","is_liked","likes"},
     "user":{"avatarLink","uuid=","user_id","user_login","user_name","user_surname"}}]

     :raises

     401(not auth):
       'err':'not auth,uuid dont active'
     400(bad request):
        'err_code':1 -parameters  not found
        'err_code':2 - given more parameters than reqired
        'err_code':3 - parameter is empty
        'err_code':4 - The post does not exist
         'err_code':100 - SQL error
     """

    cnx = mysql.connector.connect(user=bdUser, password=bdPasswd,
                                   host='localhost',
                                  database=bdName)
    cursor = cnx.cursor()

    params = ['uuid', 'post_id', 'count']
    paramsReq = list(request.args.keys())
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        app.logger.error(str(response))
        return response, 400
    if not (len(params) == len(paramsReq)):
        response = {'err_code': 2,
                    'err': f'given more parameters than reqired'}
        app.logger.error(str(response))
        return response, 400
    for item in request.args.items():
        if len(str(item[1])) == 0:
            response = {'err_code': 3,
                        'err': f'parameter {item[0]} is empty'}
            app.logger.error(str(response))
            return response, 400
    post_id = request.args.get('post_id')
    uuid = request.args.get('uuid')

    if not (checkUuid(uuid)):
        app.logger.error(str({'err': 'not auth,uuid dont active'}))
        return {'err': 'not auth,uuid dont active'}, 401

    if int(post_id) > getMaxPost():
        response = {'err_code': 4, 'err': f'The post does not exist'}  #
        app.logger.error(str(response))
        return response, 400

    count = request.args.get('count')

    id = post_id
    try:
        cursor.execute(f"SELECT DISTINCT p.post_id, p.created_at, p.DateText, p.user_id, u.user_login, u.user_name, u.user_surname, l.is_liked \
          FROM posts p \
          JOIN users u ON p.user_id = u.user_id \
          JOIN tokens AS t ON t.user_id = p.user_id  \
          LEFT JOIN (SELECT post_id AS is_liked FROM likes \
          WHERE user_id = (SELECT user_id FROM tokens WHERE token = %s) AND is_active=1) \
          AS l ON p.post_id = l.is_liked \
          WHERE (p.is_deleted = 1  or p.is_deleted_admin=1) \
                 and t.token = %s \
                \
                  AND p.post_id <= (SELECT MAX(post_id) - %s FROM posts WHERE p.is_deleted = 1) \
          ORDER BY p.post_id DESC \
          LIMIT %s;", (uuid, uuid, int(id), int(count)))
        #            #   and  p.user_id = (SELECT user_id FROM tokens WHERE token = %s)\
        # cursor.execute(f"SELECT p.post_id, p.created_at, p.DateText, p.user_id, u.user_login, u.user_name, u.user_surname \
        #     FROM posts p \
        #     JOIN users u ON p.user_id = u.user_id \
        #     JOIN tokens AS t ON t.user_id = u.user_id \
        #                            WHERE t.token  = '{uuid}' \
        #      AND p.is_deleted = 0 \
        #     AND p.post_id <= (SELECT MAX(post_id) - '{id}' FROM posts WHERE is_deleted = 0) \
        #     ORDER BY p.post_id DESC \
        #     LIMIT {count};")
        anws = {'posts': []}
        for post_id, created_at, DateText, user_id, user_login, user_name, user_surname, is_liked in cursor:
            anws['posts'].append({'post': {
                'id': post_id,
                'created_at': created_at,
                'Text': DateText,
                "image_link": f"http://{server}:{port}/postsImages/{post_id}.jpg?uuid={uuid}",
                'likes': 0,
                'is_liked': bool(not (is_liked == None))
            },

                'user': {
                    'user_id': user_id,
                    'user_login': user_login,
                    'user_name': user_name,
                    'user_surname': user_surname,
                    'avatarLink': f'http://{server}:{port}/userAvatar/{user_id}.jpg?uuid={uuid}'
                }
            })
        cnx.commit()
        for post in anws['posts']:
            likes = 0
            try:
                print(post)
                id = post['post']['id']
                print(id)
                cursor.execute(f"SELECT COUNT(DISTINCT user_id) AS likes_count \
                                             FROM likes \
                                             WHERE post_id = {id} \
                                             AND is_active = 1")
                for count in cursor:
                    likes = count[0]
            except Exception as err:
                print(err, '!!!')
            post['post'].update({'likes': likes})
        app.logger.error(str(anws))
        return anws
    except Exception as err:
        response = {'err_code': 100, 'err': f'SQL err: {err}'}  #
        app.logger.error(str(response))
        return response, 400


cors = CORS(app)
json = FlaskJSON(app)

app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False
app.config['JSON_ADD_STATUS'] = False
app.config['UPLOAD_FOLDER'] = './upload'

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False)
