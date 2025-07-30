from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <h1>🚀 Blockchain Latest News - Test Version</h1>
    <p>✅ Flask is working correctly!</p>
    <p><a href="/health">Health Check</a></p>
    <p><a href="/test-imports">Test Imports</a></p>
    '''

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'Container is running properly'}

@app.route('/test-imports')
def test_imports():
    try:
        import psycopg2
        psycopg2_status = "✅ psycopg2 imported successfully"
    except Exception as e:
        psycopg2_status = f"❌ psycopg2 import failed: {e}"
    
    return f'''
    <h1>Import Test Results</h1>
    <p>{psycopg2_status}</p>
    <p><a href="/">← Back to Home</a></p>
    '''

if __name__ == '__main__':
    print("🧪 Starting Test Flask Application...")
    app.run(host='0.0.0.0', port=5000, debug=True)
