import { useState, useRef, useEffect } from 'react';
import './index.css';

export default function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [photo, setPhoto] = useState(null);
  const [flash, setFlash] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // Initialize camera
  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      setStream(mediaStream);
    } catch (err) {
      console.error("Error accessing camera:", err);
      alert("Please allow camera access in your browser to continue.");
    }
  };

  // Attach stream to video element when it mounts
  useEffect(() => {
    if (stream && videoRef.current) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  // Stop camera stream gracefully
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  // Capture frame to base64
  const takePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      // Match canvas to video dimensions
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext('2d');
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Get base64 image data
      const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
      setPhoto(dataUrl);
      
      // Play flash animation
      setFlash(true);
      setTimeout(() => setFlash(false), 300);
      
      // Stop webcam after capture
      stopCamera();
    }
  };

  const retake = () => {
    setPhoto(null);
    startCamera();
  };

  const sendToOrchestrator = async () => {
    if (!photo) return;
    setIsUploading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/pipeline/demo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ base64_image: photo })
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Successfully sent! Pipeline tracking thread ID: ${data.thread_id}`);
      } else {
        alert("Failed to start pipeline.");
      }
    } catch (err) {
      console.error(err);
      alert("Error sending to orchestrator. Is the backend running?");
    } finally {
      setIsUploading(false);
    }
  };

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  return (
    <div className="app-container">
      <header>
        <h1>OmniLocal Lens</h1>
        <p className="subtitle">Capture your document for instant processing</p>
      </header>

      <main className="glass-panel">
        <div className="camera-container">
          {!photo ? (
            <>
              {/* Wait for user to click 'Open Camera' to show video stream */}
              {!stream ? (
                <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: '#475569' }}>
                   Camera is off
                </div>
              ) : (
                <video 
                  ref={videoRef} 
                  autoPlay 
                  playsInline 
                  muted
                />
              )}
              {flash && <div className="flash-animation"></div>}
            </>
          ) : (
            <img src={photo} alt="Captured preview" className="preview" />
          )}
          {/* Hidden canvas for image data extraction */}
          <canvas ref={canvasRef} />
        </div>

        <div className="controls">
          {!stream && !photo && (
            <button className="btn btn-primary" onClick={startCamera}>
              <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
              </svg>
              Open Camera
            </button>
          )}

          {stream && !photo && (
            <button className="btn btn-action" onClick={takePhoto}>
              <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              Capture
            </button>
          )}

          {photo && (
            <>
              <button className="btn btn-secondary" onClick={retake} disabled={isUploading}>
                <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                  <path d="M3 3v5h5"></path>
                </svg>
                Retake
              </button>
              <button className="btn btn-primary" onClick={sendToOrchestrator} disabled={isUploading}>
                <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 2L11 13"></path>
                  <path d="M22 2l-7 20-4-9-9-4 20-7z"></path>
                </svg>
                {isUploading ? "Sending..." : "Send to Flow"}
              </button>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
