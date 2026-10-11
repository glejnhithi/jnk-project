from flask import Flask, jsonify
app = Flask(__name__)

@app.get('/')
def home():
    return jsonify(message='Hello from Jenkins CI/CD on Kubernetes!', version='1.0')

@app.get('/health')
def health():
    return jsonify(status='healthy')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
