import json

from flask_json import FlaskJSON, as_json

server = '10.8.0.1'
port = '5000'
from collections import Counter
import base64
import hashlib
import io
from flask_cors import CORS, cross_origin
import uuid

from datetime import datetime, timedelta

import mysql.connector

cnx = mysql.connector.connect(user='adm', password='1qaz@WSX12',
                              host='10.8.0.1',
                              database='memes')
cursor = cnx.cursor()

from flask import Flask, redirect, url_for, request, make_response, send_file, jsonify


def createResponse(text: dict, code: int):
    res = make_response(str(text), code)
    res.headers['Content-Type'] = 'application/json'
    return res


app = Flask(__name__)


def checkUuid(uuid2):
    cursor.execute(
        f'select token  from memes.tokens where expired_at > "{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")}"')
    fl = False
    for row in cursor:
        print(row, uuid2)
        try:
            if row[0] == uuid2:
                fl = True
                print('lol')
                cnx.commit()
                break


        except Exception as err:
            print(err)
    print(fl)
    if fl:
        return True
    else:
        return False


@app.route('/auth', methods=['GET'])
@cross_origin()
@as_json
def auth():
    """authorization users with login and password  via GET request
    :args
     login : str
     password : str
   :return
        uuid - str (unique token for session for 1 day)
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
    params = ['login', 'password']
    paramsReq = list(request.args.keys())
    print(paramsReq)
    notFound = list((Counter(params) - Counter(paramsReq)).elements())
    if len(notFound) > 0:
        response = {'err_code': 1,
                    'err': f'parameters {",".join(notFound)} not found'}
        return response, 400
    if not (len(params) == len(paramsReq)):
        response = {'err_code': 2,
                    'err': f'given more parameters than reqired'}
        return response, 400
    for item in request.args.items():
        if len(str(item[1])) == 0:
            response = {'err_code': 3,
                        'err': f'parameter {item[0]} is empty'}
            return response, 400

    login = request.args.get('login')
    passwd = request.args.get('password')

    passwdSha = hashlib.sha256(base64.b64encode(passwd.encode('utf8'))).hexdigest()
    cursor.execute(f"SELECT user_id,user_passwd,ban_end FROM memes.users where user_login='{login}'")
    user_id = 0
    for row in cursor:
        user_id = row[0]
        passwdShaDb = row[1]
        ban = row[2]
    if user_id == 0:
        response = {'err_code': 6,
                    'err': f'login not found'}
        return response, 400
    cnx.commit()
    if ban != None:
        response = {'err_code': 4,
                    'err': f'user is banned'}
        return response, 400
    elif passwdShaDb != passwdSha:
        response = {'err_code': 5,
                    'err': f'password not correct'}
        return response, 400
    else:
        random_uuid = uuid.uuid4()
        current_dateTime = (datetime.now() + timedelta(days=+1)).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            f"INSERT INTO memes.tokens (token,user_id,expired_at) VALUES ('{random_uuid}','{user_id}','{current_dateTime}');")
        cnx.commit()
        response = {'uuid': f'{str(random_uuid)}'}
        #  js=str(json.loads(str(response)))
        print(str(response).replace("'", '"'))
        # return response
        res = createResponse(response, 200)
        res.headers['Content-Type'] = 'application/json'
        return response, 200


@app.route('/setLike', methods=['GET'])
@cross_origin()
def setLike():
    """set Like

     uuid : str
     post_id : str
     user_id: str
   :return

   """
    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        return 'uuid dont active'
    post_id = request.args.get('post_id')

    try:
        cursor.execute(
            f"INSERT INTO likes (post_id, user_id, is_active)  \
VALUES ( \
    '{post_id}',  \
    (SELECT user_id FROM tokens WHERE token = '{uuid}'),   1 \
);")
        cnx.commit()
    except Exception as err:
        return f"BAD: {err}"
    return 'OK'


@app.route('/downLike', methods=['GET'])
@cross_origin()
def downLike():
    """set Like

     uuid : str
     post_id : str

   :return

   """
    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        return 'uuid dont active'
    post_id = request.args.get('post_id')

    try:
        cursor.execute(
            f"UPDATE likes SET is_active = 0  \
WHERE post_id = '{post_id}' \
AND user_id = (SELECT user_id FROM tokens WHERE token = '{uuid}');")
        cnx.commit()
    except Exception as err:
        return f"BAD: {err}"
    return 'OK'


@app.route('/getUserData', methods=['GET'])
@cross_origin()
def getUserData():
    """get user data  via login or id
   :arg
     uuid: str
     user_login : str optional
     user_id : int optional
   :return
        user_id : int
        user_login : str
        user_name : str
        user_surname : str
        user_img : blob - avatar
        date_of_birth : datetime
   """

    uuid = request.args.get('uuid')
    user_id = request.args.get('user_id')
    user_login = request.args.get('user_login')
    if not (checkUuid(uuid)):
        return 'uuid dont active'
    if user_id == None and user_login == None:
        return 'user login or id not not specified'

    if user_id != None:

        cursor.execute(
            f"SELECT user_id,user_login,user_name,user_surname,user_img,date_of_birth FROM memes.users where user_id='{user_id}';")
        for user_id, user_login, user_name, user_surname, user_img, date_of_birth in cursor:
            return {"user_id": user_id, "user_login": user_login, "user_name": user_name, "user_surname": user_surname,
                    "user_img": user_img, "date_of_birth": date_of_birth}
        cnx.commit()
    if user_login != None:

        cursor.execute(
            f"SELECT user_id,user_login,user_name,user_surname,user_img,date_of_birth FROM memes.users where user_login='{user_login}';")
        for user_id, user_login, user_name, user_surname, user_img, date_of_birth in cursor:
            return {"user_id": user_id, "user_login": user_login, "user_img": user_img, "date_of_birth": date_of_birth,
                    "user_surname": user_surname, "user_name": user_name}
        cnx.commit()


@app.route('/me', methods=['GET'])
@cross_origin()
def me():
    """get user data
   :arg
     uuid: str

   :return
        user_id : int
        user_login : str
        user_name : str
        user_surname : str
        user_img : blob - avatar
        date_of_birth : datetime
   """

    uuid = request.args.get('uuid')

    if not (checkUuid(uuid)):
        return 'uuid dont active'

    cursor.execute(f"SELECT u.user_id,u.user_login, u.user_name,u.user_surname,u.date_of_birth FROM memes.users as u JOIN tokens AS t ON t.user_id = u.user_id \
                               WHERE t.token  = '{uuid}';")
    for user_id, user_login, user_name, user_surname, date_of_birth in cursor:
        return {"user_id": user_id, "user_login": user_login, "user_name": user_name, "user_surname": user_surname,
                "user_img": f'http://{server}:{port}/userAvatart/{user_id}', "date_of_birth": date_of_birth}





@app.route('/postsImages/<int:pid>.jpg', methods=['GET'])
@cross_origin()
def get_image(pid):
    '''  return image of post_id = pid'''
    cnx2 = mysql.connector.connect(user='adm', password='1qaz@WSX12',
                                   host='10.8.0.1',
                                   database='memes')
    cursor2 = cnx2.cursor()

    uuid = request.args.get('uuid')
    # if not (checkUuid(uuid)):
    #     return 'uuid dont active'
    print(pid)
    cursor2.execute(
        f"SELECT source FROM memes.posts where post_id='{pid}';")
    for source in cursor2:
        print(source[0])
        return send_file(
            io.BytesIO(source[0]),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='%s.jpg' % pid)
    cnx2.close()


@app.route('/userAvatar/<int:pid>.jpg', methods=['GET'])
@cross_origin()
def get_avatart(pid):
    '''  return image of user avatart = pid'''
    uuid = request.args.get('uuid')
    if not (checkUuid(uuid)):
        return 'uuid dont active'
    cursor.execute(
        f"SELECT user_img FROM memes.users where user_id='{pid}';")
    for source in cursor:
        print(source[0])
        return send_file(
            io.BytesIO(source[0]),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='%s.jpg' % pid)


@app.route('/addUser', methods=['GET'])
@cross_origin()
def addUser():
    """set Like


     user_login: str
     user_passwd: str
     user_name: str
     user_surname: str
     date_of_birth: str
   :return

   """
    user_login = request.args.get('user_login')
    cursor.execute(
        f"SELECT user_login FROM users;")
    logins = []
    for login in cursor:
        logins.append(login[0])
    if user_login in logins:
        return 'BAD - user login already use'
    cnx.commit()

    string = request.args.get('user_passwd')
    user_passwd = hashlib.sha256(base64.b64encode(string.encode('utf8'))).hexdigest()
    user_name = request.args.get('user_name')
    user_surname = request.args.get('user_surname')
    date_of_birth = request.args.get('date_of_birth')
    try:
        cursor.execute(
            f"INSERT INTO users (user_login, user_passwd, user_name, user_surname, date_of_birth) VALUES ('{user_login}', '{user_passwd}', '{user_name}', '{user_surname}', '{date_of_birth}');")
        cnx.commit()
    except Exception as err:
        return f"BAD: {err}"
    return 'OK'


@app.route('/getPostsGroup', methods=['GET'])
@cross_origin()
def getPostsGroup():
    """get last 20 post at id
        :arg
          uuid: str
          post_id-int
          count: int - how many posts you need

        :return
  [post]
        :raises

        """
    uuid = request.args.get('uuid')
    id = request.args.get('post_id')
    count = request.args.get('count')
    if not (checkUuid(uuid)):
        return 'uuid dont active'
    print(count)
    cursor.execute(f"SELECT p.post_id, p.created_at, p.DateText, p.user_id, u.user_login, u.user_name, u.user_surname \
FROM posts p \
JOIN users u ON p.user_id = u.user_id \
WHERE p.is_deleted = 0 \
AND p.post_id <= (SELECT MAX(post_id) - '{id}' FROM posts WHERE is_deleted = 0) \
ORDER BY p.post_id DESC \
LIMIT {count};")

    anws = {'posts': []}
    for post_id, created_at, DateText, user_id, user_login, user_name, user_surname in cursor:
        anws['posts'].append({'post': {
            'id': post_id,
            'created_at': created_at,
            'Text': DateText,
            "image_link": f"http://{server}:{port}/postsImages/{post_id}.jpg?uuid={uuid}",
            'likes': 0,
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
            cursor.execute(f"SELECT COUNT(DISTINCT user_id) AS likes_count \
                            FROM likes \
                            WHERE post_id = {id} \
                            AND is_active = 1")
            for count in cursor:
                likes = count[0]
        except Exception as err:
            print(err, '!!!')
        post['post'].update({'likes': likes})
    return anws


@app.route('/getPostsGroupUser', methods=['GET'])
@cross_origin()
def getPostsGroupUser():
    """get last 20 post of user
            :arg
              uuid: str
            :return
      [post]
            :raises

            """
    uuid = request.args.get('uuid')
    id = request.args.get('post_id')
    count = request.args.get('count')
    if not (checkUuid(uuid)):
        return 'uuid dont active'

    cursor.execute(f"SELECT p.post_id, p.created_at, p.DateText, p.user_id, u.user_login, u.user_name, u.user_surname \
        FROM posts p \
        JOIN users u ON p.user_id = u.user_id \
        JOIN tokens AS t ON t.user_id = u.user_id \
                               WHERE t.token  = '{uuid}' \
         AND p.is_deleted = 0 \
        AND p.post_id <= (SELECT MAX(post_id) - '{id}' FROM posts WHERE is_deleted = 0) \
        ORDER BY p.post_id DESC \
        LIMIT {count};")
    anws = {'posts': []}
    for post_id, created_at, DateText, user_id, user_login, user_name, user_surname in cursor:
        anws['posts'].append({'post': {
            'id': post_id,
            'created_at': created_at,
            'Text': DateText,
            "image_link": f"http://{server}:{port}/postsImages/{post_id}.jpg?uuid={uuid}",
            'likes': 0,
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
    return anws


@app.route('/getPostData', methods=['GET'])
@cross_origin()
def getPostData():
    """get Post data  via id
    :arg
      uuid: str
      post_id : int
    :return
    user_id : str - user id who created
    source : blob - image
    post_id :int - id of post
    DateText : str - post's text
    :raises

    """
    uuid = request.args.get('uuid')
    post_id = request.args.get('post_id')

    if not (checkUuid(uuid)):
        return 'uuid dont active'
    print(post_id)
    if post_id != None:
        cnx.commit()
        cursor.execute(f"SELECT user_id,post_id,DateText,is_deleted from posts where post_id={post_id};")
        for user_id, post_id, DateText, is_deleted in cursor:
            if not (is_deleted):
                print(DateText)
                return {"user_id": user_id,
                        "image_link": f"http://{server}:{port}/postsImages/{post_id}.jpg?uuid={uuid}",
                        "post_id": post_id, "DateText": DateText}
            else:
                return f"post with id= {post_id} deleted"

        cnx.commit()
    else:
        return 'post id not specified'


cors = CORS(app)
json = FlaskJSON(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['JSON_AS_ASCII'] = False
app.config['JSON_ADD_STATUS'] = False

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False)
