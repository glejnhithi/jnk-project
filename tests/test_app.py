from app.main import app

def test_health():
    response = app.test_client().get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
