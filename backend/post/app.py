import os, sys, json, jwt, requests, boto3, redis
from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_cors import CORS
from dotenv import load_dotenv
from model import *
from kafka import KafkaProducer
from s3_handler import S3File
from random import shuffle
import logging

load_dotenv()
CORS(app)

s3 = S3File(os.environ['S3_BUCKET'])
r = redis.Redis(host=os.environ['REDIS'], port=6379)

@app.route('/post/get',methods=['GET'])
def get_post():
    token = request.headers.get('Authorization')
    timestamp = request.args.get('timestamp', default=None, type=int)

    if token == None or token == "":
        return jsonify({"status":False, "message":"Empty token"}), 404

    try:
        user_dict = requests.get(os.environ['USER_MS'] + "/user/username", headers={'Authorization': token}).json()
        if timestamp is None:
            p = KafkaProducer(bootstrap_servers=[os.environ['MSK_BROKER_1'], os.environ['MSK_BROKER_2']], acks='all')
            p.send(os.environ['CELEBRITY_QUEUE_TOPIC'], key=b"celebrity", value=token.encode())
            p.flush()
            timestamp = int(datetime.now().timestamp() * 1000)
        user_id = jwt.decode(token, os.environ['PASS_SECRET'], algorithms=['HS256'], verify=False)['user_id']
        output = []
        post_json = []

        for _ in range(5):
            posts = r.lpop(user_id)
            if posts is not None:
                result = json.loads(posts.decode())
                # output.append(json.loads(posts.decode()))
                result['username'] = user_dict[str(result['user_id'])][0]
                result['name'] = user_dict[str(result['user_id'])][1]
                output.append(result)

        if len(output) < 2:
            user = requests.get(os.environ['USER_MS'] + "/user/following", headers={'Authorization': token}).json()
            posts = PostModel.query.filter(PostModel.user_id.in_(user['following']), PostModel.date < timestamp).order_by(desc(PostModel.post_id)).limit(5).all()

            for post in posts:
                msg = {}
                msg['caption'] = post.caption
                msg['date'] = post.date
                msg['post_id'] = post.post_id
                msg['post_url'] = post.post_url
                msg['user_id'] = post.user_id
                msg['username'] = user_dict[str(post.user_id)][0]
                msg['name'] = user_dict[str(post.user_id)][1]
                post_json.append(msg)
                
        output.extend(post_json)
    except Exception as e:
        return jsonify({'status':False, "message":e}), 500

    return jsonify({'status':True, "message":output}), 200

@app.route('/post/create',methods=['POST'])
def create_post():
    
    token = request.headers.get('Authorization')
    image = request.files.get('image', default=None)
    caption = request.form.get('caption', default=None, type=str)
    curr_time = int(datetime.now().timestamp() * 1000)

    if token == None or token == "":
        return jsonify({"status":False, "message":"Empty token"}), 404
    elif image is None:
        return jsonify({'status':False, "message":"Missing image"}), 404
    elif caption is None:
        return jsonify({'status':False, "message":"Missing caption"}), 404

    try:
        user_id = jwt.decode(token, os.environ['PASS_SECRET'], algorithms=['HS256'], verify=False)['user_id']
        formatted_file_name = f"{user_id}_{curr_time}.jpg"
        s3.upload_file_to_s3(image, formatted_file_name)
        post = PostModel(user_id=user_id, post_url=os.environ['S3_BUCKET_LINK']+formatted_file_name, date=curr_time, caption=caption)
        db.session.add(post)
        db.session.commit()
        post_json = json.loads(json.dumps(post, cls=AlchemyEncoder))
        user = requests.get(os.environ['USER_MS'] + "/user/celebrity", headers={'Authorization': token}).json()
        if not user['status']:
            payload = {"current_payload": post_json, "previous_payload": {}}
            p = KafkaProducer(bootstrap_servers=[os.environ['MSK_BROKER_1'],os.environ['MSK_BROKER_2']], acks='all')
            p.send(os.environ['FEED_QUEUE_TOPIC'], key=b"create", value=json.dumps(payload).encode())
            p.flush()
    except Exception as e:
        return jsonify({'status':False, "message":e}), 500

    return jsonify({'status':True, "message":post_json}), 200

@app.route('/post/update',methods=['PUT'])
def update_post():
    
    token = request.headers.get('Authorization')
    image = request.files.get('image', default=None)
    caption = request.form.get('caption', default=None, type=str)
    post_id = request.args.get('post_id', default=None, type=str)
    curr_time = int(datetime.now().timestamp() * 1000)

    if token == None or token == "":
        return jsonify({"status":False, "message":"Empty token"}), 404
    elif image is None:
        return jsonify({'status':False, "message":"Missing image"}), 404
    elif caption is None:
        return jsonify({'status':False, "message":"Missing caption"}), 404

    try:
        user_id = jwt.decode(token, os.environ['PASS_SECRET'], algorithms=['HS256'], verify=False)['user_id']
        formatted_file_name = f"{user_id}_{curr_time}.jpg"
        post = PostModel.query.filter_by(user_id=user_id, post_id=post_id).first()
        previous_post = json.loads(json.dumps(post, cls=AlchemyEncoder))
        delete_file_name = post.post_url.split(os.environ["S3_BUCKET_LINK"])[1]
        s3.delete_file_to_s3(delete_file_name)
        s3.upload_file_to_s3(image, formatted_file_name)
        post.post_url = os.environ['S3_BUCKET_LINK'] + formatted_file_name
        post.caption = caption
        db.session.commit()
        post_json = json.loads(json.dumps(post, cls=AlchemyEncoder))
        payload = {"current_payload": post_json, "previous_payload": previous_post}
        p = KafkaProducer(bootstrap_servers=[os.environ['MSK_BROKER_1'],os.environ['MSK_BROKER_2']], acks='all')
        p.send(os.environ['FEED_QUEUE_TOPIC'], key=b"update", value=json.dumps(payload).encode())
        p.flush()
    except Exception as e:
        return jsonify({'status':False, "message":e}), 500
    
    return jsonify({'status':True, "message":post_json}), 200

@app.route('/post/delete',methods=['DELETE'])
def delete_post():
    
    token = request.headers.get('Authorization')
    post_id = request.args.get('post_id', default=None, type=str)

    if token == None or token == "":
        return jsonify({"status":False, "message":"Empty token"}), 404
    elif post_id is None:
        return jsonify({'status':False, "message":"Missing post_id"}), 404

    try:
        user_id = jwt.decode(token, os.environ['PASS_SECRET'], algorithms=['HS256'], verify=False)['user_id']
        post = PostModel.query.filter_by(user_id=user_id, post_id=post_id).first()
        delete_file_name = post.post_url.split(os.environ["S3_BUCKET_LINK"])[1]
        s3.delete_file_to_s3(delete_file_name)
        previous_post = json.loads(json.dumps(post, cls=AlchemyEncoder))
        payload = {"current_payload": {}, "previous_payload": previous_post}
        p = KafkaProducer(bootstrap_servers=[os.environ['MSK_BROKER_1'],os.environ['MSK_BROKER_2']], acks='all')
        p.send(os.environ['FEED_QUEUE_TOPIC'], key=b"delete", value=json.dumps(payload).encode())
        p.flush()
        db.session.delete(post)
        db.session.commit()
    except Exception as e:
        return jsonify({'status':False, "message":e}), 500

    return jsonify({'status':True, "message":"Success"}), 200

@app.route('/post/all', methods=['GET'])
def getall():
    token = request.headers.get('Authorization')
    allPosts = []

    if token == None or token == "":
        return jsonify({"status": False, "message": "Empty token"}), 404
    
    try:
        decode_id = jwt.decode(token, os.environ['PASS_SECRET'], algorithms=['HS256'], verify=False)['user_id']
        posts = PostModel.query.filter(PostModel.user_id != decode_id).order_by(desc(PostModel.post_id)).limit(20).all()
        user = requests.get(os.environ['USER_MS'] + '/user/username', headers={'Authorization': token}).json()
        shuffle(posts)
        for post in posts:
            msg = {}
            msg['name'] = user[str(post.user_id)][1]
            msg['username'] = user[str(post.user_id)][0]
            msg['image'] = post.post_url
            msg['caption'] = post.caption
            msg['timestamp'] = post.date
            allPosts.append(msg)

    except Exception as e:
        return jsonify({'status': False, "message": e}), 500

    return jsonify({'status': True, "message": allPosts}), 200


@app.route('/post/personal', methods=['GET'])
def get_personal_post():
    token = request.headers.get('Authorization')
    username = request.args.get('username', default=None, type=str)

    if token == None or token == "":
        return jsonify({"status": False, "message": "Empty token"}), 404
    elif username == None:
        return jsonify({"status": False, "message": "Empty username"}), 404
    
    try:
        user_id = jwt.decode(token, os.environ['PASS_SECRET'], algorithms=['HS256'], verify=False)['user_id']
        user = requests.get(os.environ['USER_MS'] + '/user/stats', headers={'Authorization': token}, params={'username':username}).json()
        if not user['status']:
            return jsonify({"status": False, "message": "No such user"}), 404
        post = PostModel.query.filter_by(user_id=user["user_id"]).order_by(desc(PostModel.post_id)).all()
        post_json = json.loads(json.dumps(post, cls=AlchemyEncoder))
    except Exception as e:
        return jsonify({'status': False, "message": e}), 500
    

    return jsonify({'status': True, "message": post_json}), 200


@app.route('/')
def index():
    return jsonify({'status': True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)