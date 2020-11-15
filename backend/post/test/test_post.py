import pytest
import json
import sys
import io
sys.path.append("../")
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()


def test_create_post(app, client):

    url = '/post/create'
    data = {"caption": "test"}
    data['image'] = (io.BytesIO(b"test"), "test.jpg")
    header = {"Authorization":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.nyk-Q0SJ1yFMoO7wPsPJnNUh7KpOOQ_mqNm3S6tTZ1g"}

    response = client.post(url, data=data, content_type='multipart/form-data', headers=header)
    assert response.status_code == 200

    message = json.loads(response.get_data(as_text=True))['message']
    print("THIS IS THE MESSAGE", message)
    assert "test" == message['caption']
    assert 1 == message['user_id']
    assert 1 == message['post_id']
    assert None != message['post_url']

def test_edit_post(app, client):
    url = "/post/update?post_id=1"
    data = {"caption": "Edit text"}
    data['image'] = (io.BytesIO(b"test2"), "test2.jpg")
    header = {"Authorization":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.nyk-Q0SJ1yFMoO7wPsPJnNUh7KpOOQ_mqNm3S6tTZ1g"}
    response = client.put(url, data=data, content_type='multipart/form-data', headers=header)

    assert response.status_code == 200
    message = json.loads(response.get_data(as_text=True))['message']
    assert "Edit text" == message['caption']
    assert 1 == message['user_id']
    assert 1 == message['post_id']
    assert None != message['post_url']

def test_delete_post(app, client):
    url = "/post/delete?post_id=1"
    header = {"Authorization":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.nyk-Q0SJ1yFMoO7wPsPJnNUh7KpOOQ_mqNm3S6tTZ1g"}
    response = client.delete(url, content_type='application/x-www-form-urlencoded',headers=header)

    assert response.status_code == 200
    expected = {'status': True, "message": "Success"}
    assert expected == json.loads(response.get_data(as_text=True))
