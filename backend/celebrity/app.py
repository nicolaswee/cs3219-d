import logging, time, json, jwt, requests
from kafka import KafkaConsumer
from sqlalchemy import desc
import redis
from model import *

c = KafkaConsumer(
    os.environ['CELEBRITY_QUEUE_TOPIC'],
    bootstrap_servers=[os.environ['MSK_BROKER_1'], os.environ['MSK_BROKER_2']],
    group_id="instaclone",
    enable_auto_commit=False
)
r = redis.Redis(host=os.environ['REDIS'], port=6379)

def process():
    results = c.poll()
    c.commit()
    if results:
        for messages in results.values():
            for msg in messages:
                key = msg.key.decode()
                token = msg.value.decode()
                user_id = jwt.decode(token, os.environ['PASS_SECRET'], algorithms=['HS256'], verify=False)['user_id']
                user = requests.get(os.environ['USER_MS'] + "/user/celebrities", headers={'Authorization': token}).json()
                celebrities = user['celebrities']
                for celebrity in celebrities:
                    post = PostModel.query.filter_by(user_id=celebrity).order_by(desc(PostModel.post_id)).limit(3).all()
                    post_json = json.loads(json.dumps(post, cls=AlchemyEncoder))
                    for i in range(len(post_json)):
                        r.rpush(user_id, json.dumps(post_json[i]))
while True:
    try:
        process()
    except InterruptedError as e:
        logging.warning("Got Interrupted, shutting down: {}".format(str(e)))
        c.close()
        break
    except Exception as e:
        logging.warning('could not read from kafka: {}'.format(str(e)))
        time.sleep(1)
        