import React from "react";

function LoadingOverlay({ text }) {
  return (
    <div className="loading-overlay">
      <div>
        <div style={{ marginBottom: 6 }}>{text}</div>
        <div style={{ fontSize: 12, color: "#9ca3af" }}>
          FastAPI 서버가 8000번 포트에서 실행 중인지 확인하세요.
        </div>
      </div>
    </div>
  );
}

export default LoadingOverlay;
