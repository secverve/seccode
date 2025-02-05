from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS
from guesslang import Guess
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
import re

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'py', 'txt', 'js', 'java', 'cpp', 'c', 'go'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 1️⃣ Guesslang 기반 언어 감지 (최우선)
def detect_language_guesslang(code):
    guess = Guess()
    try:
        detected_language = guess.language_name(code)
        return detected_language if detected_language else "Unknown"
    except Exception as e:
        print(f"Guesslang 오류 발생: {e}")
        return "Unknown"

# 2️⃣ Pygments 기반 언어 감지 (Guesslang이 특정 언어로 오탐할 경우만 사용)
def detect_language_pygments(code):
    try:
        lexer = guess_lexer(code)
        return lexer.name
    except ClassNotFound:
        return "Unknown"

# 3️⃣ 정규식 기반 언어 감지 (Guesslang + Pygments가 실패할 경우 보조 역할)
def detect_language_regex(code):
    patterns = {
        'Python': [r'def\s+\w+\(', r'import\s+\w+', r'print\s*\(', r'if\s+__name__\s*==\s*["\']__main__["\']'],
        'JavaScript': [r'function\s+\w+\(', r'console\.log\(', r'var\s+\w+\s*=', r'let\s+\w+\s*='],
        'Java': [r'public\s+class\s+\w+', r'public\s+static\s+void\s+main', r'System\.out\.println'],
        'C': [r'#include\s+<\w+>', r'int\s+main\s*\(\)', r'printf\s*\('],
        'C++': [r'#include\s+<\w+>', r'std::cout\s*<<', r'int\s+main\s*\(\)'],
        'Go': [r'package\s+main', r'func\s+main\(\)', r'import\s+"fmt"'],
    }

    for language, keywords in patterns.items():
        if any(re.search(keyword, code, re.IGNORECASE) for keyword in keywords):
            return language

    return "Unknown"

# ✅ 최종 언어 감지 (1️⃣ Guesslang → 2️⃣ Pygments (YAML, Text Only 예외 처리) → 3️⃣ 정규식)
def detect_language(code):
    language = detect_language_guesslang(code)
    # 🔥 Guesslang이 특정 오탐 언어(YAML, Text Only, Tera Term macro)로 감지되면 Pygments 사용
    if language in ["Groovy", "Unknown", "YAML", "Text only", "Tera Term macro"]:
        language = detect_language_pygments(code)

    # 🔥 Pygments가 "Text Only"로 감지되면 정규식 사용
    if language == "Text only":
        language = detect_language_regex(code)

    return language

@app.route('/analyze-code', methods=['POST'])
def analyze_code():
    data = request.get_json()
    code = data.get('code', '')

    if not code:
        return jsonify({'error': '코드가 제공되지 않았습니다.'}), 400

    detected_language = detect_language(code)

    return jsonify({
        'language': detected_language
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '파일이 제공되지 않았습니다.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        detected_language = detect_language(code)

        return jsonify({
            'fileName': filename,
            'message': '파일 분석 완료',
            'language': detected_language
        })

    return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400

if __name__ == '__main__':
    app.run(debug=True)
