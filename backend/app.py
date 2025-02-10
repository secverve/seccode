from flask import Flask, request, jsonify
import os
import subprocess
import tempfile
import json
import google.generativeai as genai  # ✅ Google Gemini API
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"py", "txt"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ✅ Google Gemini API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "your-gemini-api-key"  # 환경 변수에서 가져오도록 변경 가능

genai.configure(api_key=GEMINI_API_KEY)

# ✅ 번역기 (deep-translator 사용)
def translate_text(text):
    try:
        return GoogleTranslator(source="en", target="ko").translate(text)
    except Exception as e:
        print(f"⚠️ [ERROR] 번역 실패: {e}")
        return text  # 번역 실패 시 원본 반환

# ✅ Google Gemini 기반 해결책 생성
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
    except Exception as e:
        print(f"⚠️ [ERROR] Gemini 해결책 생성 실패: {e}")
        return "✅ 해결책: 보안 권장 사항을 검토하세요."

# ✅ Bandit 기반 취약점 분석
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

            # ✅ 취약한 코드 가져오기
            vulnerable_code = "취약한 코드 없음"
            if "code" in issue and isinstance(issue["code"], list):
                vulnerable_code = "\n".join(issue["code"])

            # ✅ Gemini 기반 해결책 생성
            suggested_fix = generate_fix_with_gemini(translated_description, vulnerable_code)

            vulnerabilities.append({
                "type": test_id,
                "code": vulnerable_code,
                "description": translated_description,
                "solution": suggested_fix,
            })

        return vulnerabilities
    finally:
        os.remove(temp_file_path)

@app.route("/analyze-code", methods=["POST"])
def analyze_code():
    data = request.get_json()
    code = data.get("code", "")

    if not code:
        return jsonify({"error": "코드가 제공되지 않았습니다."}), 400

    vulnerabilities = analyze_with_bandit(code)

    return jsonify({
        "vulnerabilities": vulnerabilities
    })

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "파일이 제공되지 않았습니다."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "파일이 선택되지 않았습니다."}), 400

    if file and file.filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS:
        filename = file.filename
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        vulnerabilities = analyze_with_bandit(code)

        return jsonify({
            "fileName": filename,
            "message": "파일 분석 완료",
            "vulnerabilities": vulnerabilities
        })

    return jsonify({"error": "허용되지 않는 파일 형식입니다."}), 400

if __name__ == "__main__":
    app.run(debug=True)
