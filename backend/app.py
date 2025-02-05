from flask import Flask, request, jsonify
import os
import re
from werkzeug.utils import secure_filename
from flask_cors import CORS
from guesslang import Guess
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'py', 'txt', 'js', 'java', 'cpp', 'c', 'go'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 1차: Guesslang을 이용한 언어 감지
def detect_language_guesslang(code):
    guess = Guess()
    detected_language = guess.language_name(code)
    return detected_language if detected_language else "Unknown"

# 2차: Pygments를 이용한 언어 감지 (Guesslang이 실패할 경우만 사용)
def detect_language_pygments(code):
    try:
        lexer = guess_lexer(code)
        return lexer.name
    except ClassNotFound:
        return "Unknown"

# 3차: 정규식을 이용한 언어 감지 (특정 조건 만족 시 보조적 사용)
def detect_language_regex(code):
    patterns = {
        'Go': [r'package\s+main', r'func\s+main\s*\(\)', r'fmt\.Println\(', r'import\s+"fmt"'],
        'C': [r'#include', r'int main\s*\(.*\)', r'printf\(', r'scanf\('],
        'Java': [r'public class ', r'void main\s*\(String\[\] args\)', r'System.out.println\('],
    }
    for language, keywords in patterns.items():
        if any(re.search(keyword, code) for keyword in keywords):
            return language
    return "Unknown"

# 통합된 언어 감지 함수 (Guesslang 우선, 보조적으로 Pygments + 정규식 활용)
def detect_language(code):
    language = detect_language_guesslang(code)
    if language == "Unknown" or language in ["Python", "JavaScript"]:
        language = detect_language_pygments(code)
    if language == "Unknown":
        language = detect_language_regex(code)
    return language

@app.route('/analyze-code', methods=['POST'])
def analyze_code():
    data = request.get_json()
    code = data.get('code', '')
    
    if not code:
        return jsonify({'error': '코드가 제공되지 않았습니다.'}), 400
    
    detected_language = detect_language(code)  # Guesslang + Pygments + 정규식 조합
    
    return jsonify({
        'language': detected_language  # 감지된 언어 반환
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
        
        detected_language = detect_language(code)  # Guesslang + Pygments + 정규식 조합
        
        return jsonify({
            'fileName': filename,
            'message': '파일 분석 완료',
            'language': detected_language  # 감지된 언어 반환
        })
    
    return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400

if __name__ == '__main__':
    app.run(debug=True)
