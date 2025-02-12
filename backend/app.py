import json
import subprocess
import tempfile
import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from deep_translator import GoogleTranslator
from guesslang import Guess
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
import sys

app = Flask(__name__)
CORS(app)

sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ✅ Google Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# ✅ 업로드 폴더를 프로젝트 폴더 밖으로 분리 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"py", "txt", "js", "java", "cpp", "c", "go"}

# ✅ 언어 감지 (Guesslang → Pygments → 정규식)
def detect_language(code):
    language = detect_language_guesslang(code)
    if language in ["YAML", "Groovy", "Unknown", "Text only"]:
        language = detect_language_pygments(code)
    if language == "Text only":
        language = detect_language_regex(code)
    return language

def detect_language_guesslang(code):
    guess = Guess()
    try:
        return guess.language_name(code) or "Unknown"
    except Exception:
        return "Unknown"

def detect_language_pygments(code):
    try:
        lexer = guess_lexer(code)
        return lexer.name
    except ClassNotFound:
        return "Unknown"

def detect_language_regex(code):
    patterns = {
        "Python": [r"def\s+\w+\(", r"import\s+\w+", r"print\s*\(", r"if\s+__name__\s*==\s*['\"]__main__['\"]"],
        "JavaScript": [r"function\s+\w+\(", r"console\.log\(", r"var\s+\w+\s*=", r"let\s+\w+\s*="],
        "Java": [r"public\s+class\s+\w+", r"public\s+static\s+void\s+main", r"System\.out\.println"],
        "C": [r"#include\s+<\w+>", r"int\s+main\s*\(\)", r"printf\s*\("],
        "C++": [r"#include\s+<\w+>", r"std::cout\s*<<", r"int\s+main\s*\(\)"],
        "Go": [r"package\s+main", r"func\s+main\(\)", r"import\s+\"fmt\""],
    }
    for language, keywords in patterns.items():
        if any(re.search(keyword, code, re.IGNORECASE) for keyword in keywords):
            return language
    return "Unknown"

# ✅ Bandit 취약점 분석
def analyze_with_bandit(code):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name
    try:
        bandit_cmd = ["bandit", "-r", temp_file_path, "-f", "json"]
        result = subprocess.run(bandit_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode not in [0, 1]:
            return [{"error": "Bandit 분석 중 오류 발생"}]
        bandit_output = json.loads(result.stdout)
        vulnerabilities = []
        for issue in bandit_output.get("results", []):
            test_id = issue.get("test_id", "Unknown")
            description = issue.get("issue_text", "N/A")
            translated_description = translate_text(description)
            raw_code = issue.get("code", "취약한 코드 없음")
            formatted_code = decode_bandit_code(raw_code)
            suggested_fix = generate_fix_with_gemini(translated_description, formatted_code)
            vulnerabilities.append({
                "type": test_id,
                "code": formatted_code,
                "description": translated_description,
                "solution": suggested_fix,
            })
        return vulnerabilities
    finally:
        os.remove(temp_file_path)

# ✅ Bandit 코드 정리 (가독성 향상)
def decode_bandit_code(raw_code):
    lines = raw_code.split("\n")
    clean_code = "\n".join([line.split(" ", 1)[-1] if " " in line else line for line in lines])
    return clean_code.replace("\\u274c", "❌").strip()

# ✅ 번역 함수 
def translate_text(text):
    try:
        return GoogleTranslator(source="en", target="ko").translate(text)
    except Exception:
        return text

# ✅ Gemini 기반 해결책 생성
def generate_fix_with_gemini(description, vulnerable_code):
    prompt = f"""
    아래의 코드는 보안 취약점이 감지된 코드입니다:

    취약한 코드:
    ```python
    {vulnerable_code}
    ```

    취약점 설명:
    {description}

    이 문제를 해결하려면 어떻게 수정해야 할까요?
    올바른 보안 패턴을 사용하여 이 문제를 해결하는 코드 예제를 제시하세요.
    """
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return f"✅ Gemini 추천 해결책:\n{response.text}"
    except Exception:
        return "✅ 해결책: 보안 권장 사항을 검토하세요."

# ✅ Flask 엔드포인트 (코드 분석)
@app.route("/analyze-code", methods=["POST"])
def analyze_code():
    data = request.get_json()
    code = data.get("code", "")
    if not code:
        return jsonify({"error": "코드가 제공되지 않았습니다."}), 400
    detected_language = detect_language(code)
    vulnerabilities = analyze_with_bandit(code)
    return jsonify({
        "language": detected_language,
        "vulnerabilities": vulnerabilities
    })

# ✅ 파일 업로드 기능
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "파일이 제공되지 않았습니다."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
    if file and allowed_file(file.filename):
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        with open(filename, "r", encoding="utf-8") as f:
            code = f.read()
        detected_language = detect_language(code)
        vulnerabilities = analyze_with_bandit(code)
        return jsonify({
            "fileName": file.filename,
            "message": "파일 분석 완료",
            "language": detected_language,
            "vulnerabilities": vulnerabilities
        })
    return jsonify({"error": "허용되지 않는 파일 형식입니다."}), 400

if __name__ == "__main__":
    app.run(debug=True)