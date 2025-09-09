from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        # Make request to Ollama API
        ollama_response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'mistral',
                'prompt': message,
                'stream': True
            },
            stream=True
        )
        
        def generate():
            for line in ollama_response.iter_lines():
                if line:
                    try:
                        json_data = json.loads(line.decode('utf-8'))
                        if 'response' in json_data:
                            yield f"data: {json_data['response']}\n\n"
                        if json_data.get('done', False):
                            yield "data: [DONE]\n\n"
                            break
                    except json.JSONDecodeError:
                        continue
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Failed to connect to Ollama'}), 500

if __name__ == '__main__':
    print("✅ Streaming server running at http://localhost:3000")
    app.run(host='0.0.0.0', port=3000, debug=True)
