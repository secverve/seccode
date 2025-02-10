import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import "./App.css";

function App() {
    const [code, setCode] = useState("");
    const [vulnerabilities, setVulnerabilities] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [language, setLanguage] = useState("");

    const analyzeCode = () => {
        fetch("http://localhost:5000/analyze-code", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code }),
        })
        .then((response) => response.json())
        .then((data) => {
            setLanguage(`언어 감지: ${data.language}`);
            setVulnerabilities(data.vulnerabilities || []);
        })
        .catch((error) => console.error("❌ [ERROR] 코드 분석 요청 실패:", error));
    };

    const handleFileUpload = () => {
        if (selectedFile) {
            const formData = new FormData();
            formData.append("file", selectedFile);

            fetch("http://localhost:5000/upload", {
                method: "POST",
                body: formData,
            })
            .then((response) => response.json())
            .then((data) => {
                setLanguage(`언어 감지: ${data.language}`);
                setVulnerabilities(data.vulnerabilities || []);
            })
            .catch((error) => console.error("❌ [ERROR] 파일 업로드 실패:", error));
        }
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
                        <input
                            type="file"
                            onChange={(e) => setSelectedFile(e.target.files[0])}
                        />
                        <button onClick={handleFileUpload} className="upload-button">
                            업로드
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
