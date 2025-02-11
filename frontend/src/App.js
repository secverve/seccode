import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import "./App.css";

const FILE_LANGUAGES = {
    py: "python",
    js: "javascript",
    java: "java",
    cpp: "c++",
    c: "c",
    go: "go",
};

function App() {
    const [code, setCode] = useState("");
    const [vulnerabilities, setVulnerabilities] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [language, setLanguage] = useState("");

    // 코드 직접 입력 후 분석
    const analyzeCode = () => {
        fetch("http://localhost:5000/analyze-code", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code }),
        })
        .then((response) => response.json())
        .then((data) => {
            console.log("📢 코드 분석 결과:", data); // ✅ 응답 확인
            setLanguage(`언어 감지: ${data.language}`);
            setVulnerabilities(data.vulnerabilities || []);
        })
        .catch((error) => console.error("❌ [ERROR] 코드 분석 요청 실패:", error));
    };

    // 파일 선택 시 Monaco Editor에 자동 반영 + 언어 감지
    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);

            // 파일 확장자로 언어 감지
            const fileExt = file.name.split(".").pop().toLowerCase();
            const detectedLanguage = FILE_LANGUAGES[fileExt] || "plaintext";

            const reader = new FileReader();
            reader.onload = (e) => {
                setCode(e.target.result); // Monaco Editor에 파일 내용 반영
                setLanguage(`📌 감지된 언어: ${detectedLanguage}`);
            };
            reader.readAsText(file);
        }
    };

    // 파일 업로드 후 자동 분석
    const uploadAndAnalyzeFile = () => {
        if (!selectedFile) {
            console.error("❌ [ERROR] 파일이 선택되지 않았습니다.");
            return;
        }

        const formData = new FormData();
        formData.append("file", selectedFile);

        fetch("http://localhost:5000/upload", {
            method: "POST",
            body: formData,
        })
        .then((response) => response.json())
        .then((data) => {
            console.log("📢 [프론트엔드] 파일 업로드 응답:", data); // ✅ 업로드 응답 확인
            setLanguage(`언어 감지 (업로드): ${data.language}`);  // ✅ 업로드에서 감지된 언어 표시
        
            // 📌 업로드 후 자동으로 코드 분석 실행
            fetch("http://localhost:5000/analyze-code", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code }),
            })
            .then((response) => response.json())
            .then((analysisData) => {
                console.log("📢 [프론트엔드] 분석 결과:", analysisData); // ✅ 분석 응답 확인
                setLanguage(`언어 감지 (분석): ${analysisData.language}`);  // ✅ 분석에서 감지된 언어 표시
                setVulnerabilities(analysisData.vulnerabilities || []);
            })
            .catch((error) => console.error("❌ [ERROR] 코드 분석 요청 실패:", error));
        })
        .catch((error) => console.error("❌ [ERROR] 파일 업로드 실패:", error));
    };

    return (
        <div className="App">
            <div className="split left">
                <div className="input-container">
                    <h2>소스코드 입력</h2>
                    <Editor
                        height="500px"
                        width="100%"
                        defaultLanguage="python"
                        theme="vs-dark"
                        value={code}
                        onChange={(value) => setCode(value)}
                        options={{
                            automaticLayout: true,
                            minimap: { enabled: false },
                            fontSize: 14,
                        }}
                    />
                    <button className="analyze-button" onClick={analyzeCode}>
                        코드 분석
                    </button>

                    <div className="file-upload-container">
                        <h2>파일 업로드</h2>
                        <input type="file" onChange={handleFileUpload} />
                        <button onClick={uploadAndAnalyzeFile} className="upload-button">
                            업로드 및 분석
                        </button>
                    </div>
                </div>
            </div>

            <div className="split right">
                <div className="output-container">
                    <h2>분석 결과</h2>
                    <p>{language}</p>

                    {vulnerabilities.length > 0 ? (
                        <div className="vulnerabilities">
                            <h3>🛡️ 보안 취약점 목록</h3>
                            <ul>
                                {vulnerabilities.map((vuln, index) => (
                                    <li key={index} className="vulnerability-item">
                                        <strong>🚨 취약점 유형:</strong> {vuln.type}
                                        <br />
                                        <strong>📌 코드:</strong>
                                        <pre className="vulnerable-code">{vuln.code}</pre>
                                        <br />
                                        <strong>📝 설명:</strong> {vuln.description}
                                        <br />
                                        <strong>🛠 해결책:</strong>
                                        <pre className="solution-text">{vuln.solution}</pre>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ) : (
                        <p>🔍 취약점이 감지되지 않았습니다.</p>
                    )}
                </div>
            </div>
        </div>
    );
}

export default App;
