from flask import Flask, request, Response, jsonify
from flask import send_from_directory
from flask_cors import CORS
import requests
import json

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        lang = data.get('lang', 'auto')

        # Simple auto-detection: Hindi (Devanagari) / Sikkimese (Tibetan) / Nepali (Devanagari) / Lepcha (U+1C00–U+1C4F) / English
        if lang == 'auto':
            if any('\u0900' <= ch <= '\u097F' for ch in message):
                # Could be Hindi or Nepali; prefer Nepali if common Nepali markers present
                if any(token in message for token in ['छ', 'छन्', 'भयो', 'उहाँ', 'तपाईं']):
                    lang = 'ne'  # Nepali
                else:
                    lang = 'hi'  # Hindi
            elif any('\u0F00' <= ch <= '\u0FFF' for ch in message):
                lang = 'si'  # Tibetan block often used for Sikkimese
            elif any('\u1C00' <= ch <= '\u1C4F' for ch in message):
                lang = 'lep'  # Lepcha script
            else:
                lang = 'en'

        # Strong system prompts per language
        if lang == 'hi':
            system_instruction = (
                "आप एक सहायक यात्रा सहायक हैं। कृपया सभी उत्तर शुद्ध और स्वाभाविक हिन्दी (देवनागरी लिपि) में दें। "
                "ट्रांसलिटरेशन (Hinglish) का प्रयोग न करें। संक्षिप्त, शिष्ट और स्पष्ट वाक्य लिखें (2–4 वाक्य)। "
                "जहाँ सम्भव हो वहाँ स्थानीय शब्दों/मात्राओं का सही प्रयोग करें। बिंदुवार उत्तर देने की आवश्यकता हो तो छोटे बुलेट प्रयोग करें। "
                "अंग्रेज़ी शब्दों से बचें; केवल आवश्यक नाम/उपाधियाँ ही मूल रूप में रखें।"
            )
        elif lang == 'si':
            # Sikkimese (Bhutia) uses Tibetan script; keep sentences short, interactive, and polite
            system_instruction = (
                "ཁྱེད་རང་འཇམ་སྙན་གྱི་སྐད་ཆ་བྱེད་པའི་ཤེས་རིག་འཚོལ་ཞིབ་ཡིན། ལག་ལེན་བྱ་སྟངས་དང་ལམ་སྟོན་གསལ་བོར་བརྗོད། "
                "སྐད་ཡིག་གངས་ཡུལ་སྐད་ (སིཀིམ་སྐད་/བོད་རིགས་ Bhutia) སྤྱོད་པར་བྱ། དུས་སུ་བོད་ཡིག་རྩོམ་སྒྲིག་ལྟར་སྒྲིག་འཛུགས་བྱེད། "
                "ལེགས་པོའི་ཚིག་གིས་བསྡུ་དགོས་(2–4 ཚིག) དང་དོན་གསལ་བ་ལ་སྐད་ཆ་སླ་བ་སྤྱད། བརྒྱུད་སྐད་ (Tibetan dialect) ལ་མཐུན་པར་བརྗོད།"
            )
        elif lang == 'ne':
            # Nepali (Devanagari) – polite, tour-focused, clear
            system_instruction = (
                "तपाईं एक सहयोगी यात्रा सहायक हुनुहुन्छ। कृपया सबै जवाफ शुद्ध र स्पष्ट नेपाली भाषामा दिनुहोस्। "
                "हिन्दी/अंग्रेजी ट्रान्सलिटरेशन नगर्नुहोस्। छोटो (2–4 वाक्य), शिष्ट, र इन्टरेक्टिभ बनाउनुहोस्; आवश्यक परेमा साना बुलेट प्रयोग गर्नुहोस्।"
            )
        elif lang == 'lep':
            # Lepcha – not all models have strong support; guide clarity and fallback if script unsupported
            system_instruction = (
                "Kū Róng (Lepcha) language: keep answers concise (2–4 sentences), clear and polite. "
                "If Lepcha script support is limited, reply in simple English while preserving Lepcha names and terms."
            )
        else:  # 'en'
            system_instruction = (
                "You are a helpful travel assistant. Respond clearly and naturally in English. "
                "Use concise sentences and correct grammar."
            )

        # Compose request payload using 'system' for better control
        payload = {
            'model': 'mistral',
            'system': system_instruction,
            'prompt': message,
            'stream': True,
            'options': {
                'temperature': 0.35,
                'top_p': 0.9,
                'repeat_penalty': 1.17,
                'num_ctx': 4096
            }
        }
        
        # Make request to Ollama API
        ollama_response = requests.post(
            'http://localhost:11434/api/generate',
            json=payload,
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
