import logging, time, json
from kafka import KafkaConsumer
import redis
from model import *

c = KafkaConsumer(
    os.environ['FEED_QUEUE_TOPIC'],
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
                value = json.loads(msg.value.decode())
                current_payload = value['current_payload']
                previous_payload = value['previous_payload']
                user = UsersModel.query.filter_by(user_id=current_payload['user_id']).first()
                followers = user.followers
                if key == "create":
                    for follower in followers:
                        r.rpush(follower, json.dumps(current_payload))
                elif key == "update":
                    for follower in followers:
                        r.lrem(follower, 1, json.dumps(previous_payload))
                        r.rpush(follower, json.dumps(current_payload))
                elif key == "delete":
                    for follower in followers:
                        r.lrem(follower, 1, json.dumps(previous_payload))
                        
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