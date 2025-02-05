import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import './App.css';

function App() {
    const [code, setCode] = useState('');
    const [feedback, setFeedback] = useState('');
    const [language, setLanguage] = useState('');
    const [vulnerabilities, setVulnerabilities] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileFeedback, setFileFeedback] = useState('');

    const analyzeCode = () => {
        setLoading(true);
        fetch('http://localhost:5000/analyze-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        })
        .then(response => response.json())
        .then(data => {
            setFeedback(data.bandit_analysis || '보안 취약점 없음');
            setLanguage(`언어 감지: ${data.language}`);
            setVulnerabilities(data.pylint_analysis ? data.pylint_analysis.split('\n') : []);
        })
        .catch(error => {
            console.error('❌ 오류 발생:', error);
            setFeedback('서버에서 오류가 발생했습니다.');
            setLanguage('언어 감지 실패');
            setVulnerabilities([]);
        })
        .finally(() => setLoading(false));
    };

    const handleFileUpload = () => {
        if (selectedFile) {
            const formData = new FormData();
            formData.append('file', selectedFile);

            fetch('http://localhost:5000/upload', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                setFileFeedback(`파일 이름: ${data.fileName}, 결과: ${data.message}`);
                setFeedback(data.highlightedCode || '분석 결과를 여기에 표시합니다.');
                setLanguage(`언어: ${data.language}`);
                setVulnerabilities(data.feedback || []);
            })
            .catch(error => {
                console.error('Error:', error);
                setFileFeedback('파일 업로드 중 오류가 발생했습니다.');
                setFeedback('');
                setLanguage('');
                setVulnerabilities([]);
            });
        } else {
            setFileFeedback('업로드할 파일을 선택하세요.');
        }
    };

    return (
        <div className="App dark-theme">
            <div className="split left">
                <div className="input-container" style={{ width: '100%', height: '100%' }}>
                    <h2>소스코드 입력</h2>
                    <Editor
                        height="500px"
                        width="100%"
                        defaultLanguage="javascript"
                        theme="vs-dark" // 어두운 테마 적용
                        options={{
                            fontSize: 14,
                            minimap: { enabled: false },
                            automaticLayout: true,
                            suggestOnTriggerCharacters: true,
                            wordBasedSuggestions: true,
                            quickSuggestions: true,
                            cursorBlinking: "smooth",
                            fontLigatures: true,
                            renderWhitespace: "all",
                            renderLineHighlight: "all",
                            scrollbar: {
                                vertical: "visible",
                                horizontal: "visible"
                            },
                            overviewRulerBorder: false
                        }}
                        value={code}
                        onChange={(value) => setCode(value)}
                    />
                    <button onClick={analyzeCode} disabled={loading}>
                        {loading ? '분석 중...' : '코드 분석'}
                    </button>
                    <div className="file-upload-container">
                        <h2>파일 업로드</h2>
                        <input
                            type="file"
                            onChange={(e) => setSelectedFile(e.target.files[0])}
                        />
                        <button onClick={handleFileUpload} className="upload-button">업로드</button>
                    </div>
                </div>
            </div>
            <div className="split right">
                <div className="output-container" style={{ width: '100%', height: '100%' }}>
                    <h2>분석 결과</h2>
                    <p>{language}</p>
                    <div className="code-output">
                        <pre>{feedback}</pre>
                    </div>
                    {vulnerabilities.length > 0 && (
                        <div className="vulnerabilities">
                            <h3>코드 스타일 및 보안 경고</h3>
                            <ul>
                                {vulnerabilities.map((vuln, index) => (
                                    <li key={index}>{vuln}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    <div className="feedback">
                        <h3>파일 검사 결과:</h3>
                        <p>{fileFeedback}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;