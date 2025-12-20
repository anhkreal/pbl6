import React, { useEffect, useRef, useState } from 'react';
import * as faceapi from 'face-api.js';
import StaffLayout from '../../layouts/StaffLayout';
import ErrorBanner from '../../components/ErrorBanner';
import { apiFetch } from '../../api/http';
import { buildUrl } from '../../api/base';
declare global {
  interface Window {
    cv: any;
  }
}

const POSITIONS = [
  { key: 'frontal1', label: 'Chính diện 1' },
  { key: 'frontal2', label: 'Chính diện 2' },
  { key: 'left', label: 'Trái' },
  { key: 'right', label: 'Phải' },
  { key: 'left_top', label: 'Trái trên' },
  { key: 'right_top', label: 'Phải trên' },
  { key: 'left_bottom', label: 'Trái dưới' },
  { key: 'right_bottom', label: 'Phải dưới' },
  { key: 'up', label: 'Ngẩng lên' },
  { key: 'down', label: 'Nhìn xuống' },
];

const LABEL_BY_KEY: Record<string, string> = POSITIONS.reduce((acc, p) => {
  acc[p.key] = p.label;
  return acc;
}, {} as Record<string, string>);

export default function ImageUpdate() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [images, setImages] = useState<Record<string, string>>({});
  const [countdown, setCountdown] = useState<number | null>(null);
  const [mockUploading, setMockUploading] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [facesLoading, setFacesLoading] = useState(false);
  const [facesError, setFacesError] = useState('');
  const [existingFaces, setExistingFaces] = useState<string[]>([]);

  function getSessionUserId(): number | null {
    try {
      const raw = sessionStorage.getItem('userId');
      if (!raw) return null;
      const n = Number(raw);
      return Number.isNaN(n) ? null : n;
    } catch {
      return null;
    }
  }

  async function loadExistingFaces() {
    const userId = getSessionUserId();
    if (!userId) { setExistingFaces([]); return; }
    setFacesLoading(true); setFacesError('');
    try {
      const res: any = await apiFetch(`/faces/${userId}?include_image_base64=true`);
      const arr: any[] = Array.isArray(res?.faces) ? res.faces : [];
      const imgs = arr
        .map((f: any) => (f?.image_base64 || f?.image || '').toString().trim())
        .filter((s: string) => !!s)
        .map((s: string) => (s.startsWith('data:image') || s.startsWith('http')) ? s : `data:image/jpeg;base64,${s}`)
        .slice(0, 10);
      setExistingFaces(imgs);
    } catch (e: any) {
      setFacesError(e?.message || 'Không tải được danh sách ảnh');
      setExistingFaces([]);
    } finally {
      setFacesLoading(false);
    }
  }

  useEffect(() => {
    // Load face-api.js models song song, khi xong thì setModelLoaded(true)
    Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri('/model'),
      faceapi.nets.faceLandmark68Net.loadFromUri('/model')
    ]).then(() => setModelLoaded(true));
    let mounted = true;
    let localStream: MediaStream | null = null;
    (async () => {
      try {
        const s = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        if (!mounted) { s.getTracks().forEach(t => t.stop()); return; }
        setStream(s);
        localStream = s;
        if (videoRef.current) videoRef.current.srcObject = s;
      } catch (e) {
        console.error('camera init', e);
      }
    })();
    return () => {
      mounted = false;
      // Dừng stream khi rời trang hoặc unmount
      if (localStream) localStream.getTracks().forEach(t => t.stop());
      if (videoRef.current) videoRef.current.srcObject = null;
    };
  }, []);

  // Load existing faces once on mount
  useEffect(() => {
    loadExistingFaces();
  }, []);

  useEffect(() => {
    if (countdown === null) return;
    if (countdown === 0) {
      doCapture();
      setCountdown(null);
      return;
    }
    const t = setTimeout(() => setCountdown(c => (c! - 1)), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  async function doCapture() {
    if (!modelLoaded) {
      alert('Model nhận diện khuôn mặt chưa sẵn sàng. Vui lòng đợi!');
      return;
    }
    const v = videoRef.current;
    const c = canvasRef.current;
    if (!v || !c) return;
    c.width = v.videoWidth || 640;
    c.height = v.videoHeight || 480;
    const ctx = c.getContext('2d')!;
    ctx.drawImage(v, 0, 0, c.width, c.height);

    // Helper: decorate cropped face with border + label (similar to Python overlay)
    function decorateFaceCanvas(faceCanvas: HTMLCanvasElement, label: string) {
      const ctx2 = faceCanvas.getContext('2d');
      if (!ctx2) return;
      const w = faceCanvas.width;
      const h = faceCanvas.height;
      ctx2.save();
      // Border: green like recognized rectangle
      ctx2.lineWidth = Math.max(2, Math.floor(Math.min(w, h) * 0.02));
      ctx2.strokeStyle = '#00C853';
      ctx2.strokeRect(1, 1, w - 2, h - 2);
      // Label background + text (top-left)
      const padX = 6;
      const padY = 4;
      const fontSize = Math.max(10, Math.floor(Math.min(w, h) * 0.08));
      ctx2.font = `${fontSize}px sans-serif`;
      const metrics = ctx2.measureText(label);
      const textW = metrics.width;
      const textH = fontSize; // approximate height
      ctx2.fillStyle = 'rgba(0,0,0,0.55)';
      ctx2.fillRect(0, 0, textW + padX * 2, textH + padY * 2);
      ctx2.fillStyle = '#FFFFFF';
      ctx2.textBaseline = 'top';
      ctx2.fillText(label, padX, padY);
      ctx2.restore();
    }

    // Helper: create padded gray square (rgb(114,114,114)) and resize to 512x512 like Python prepare_face_image()
    function createPaddedCanvas(srcCanvas: HTMLCanvasElement, targetSize = 512, marginPercent = 0.5) {
      const w = srcCanvas.width;
      const h = srcCanvas.height;
      const marginW = Math.floor(w * marginPercent);
      const marginH = Math.floor(h * marginPercent);
      const canvasSize = Math.max(w, h) + Math.max(marginW, marginH) * 2;

      // Step 1: center face on gray padded square
      const square = document.createElement('canvas');
      square.width = canvasSize;
      square.height = canvasSize;
      const sctx = square.getContext('2d')!;
      sctx.fillStyle = 'rgb(114,114,114)';
      sctx.fillRect(0, 0, canvasSize, canvasSize);
      const startX = Math.floor((canvasSize - w) / 2);
      const startY = Math.floor((canvasSize - h) / 2);
      sctx.drawImage(srcCanvas, startX, startY);

      // Step 2: resize to target (512x512)
      const out = document.createElement('canvas');
      out.width = targetSize;
      out.height = targetSize;
      const octx = out.getContext('2d')!;
      octx.imageSmoothingEnabled = true;
      octx.imageSmoothingQuality = 'high';
      octx.drawImage(square, 0, 0, targetSize, targetSize);
      return out;
    }

    // Helper: classify pose into 10 categories using face landmarks
    async function classifyPoseFromCanvas(canvasEl: HTMLCanvasElement): Promise<string | null> {
      try {
        const det = await faceapi
          .detectSingleFace(canvasEl, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.2 }))
          .withFaceLandmarks();
        if (!det || !det.landmarks) return null;
        const lm = det.landmarks;
        const pts = lm.positions as { x: number; y: number }[];
        const leftEyeIdx = [36, 37, 38, 39, 40, 41];
        const rightEyeIdx = [42, 43, 44, 45, 46, 47];
        const chinIdx = 8;
        const noseTipIdx = 30;
        function avg(indexes: number[]) {
          let sx = 0, sy = 0;
          indexes.forEach(i => { sx += pts[i].x; sy += pts[i].y; });
          return { x: sx / indexes.length, y: sy / indexes.length };
        }
        const leftEye = avg(leftEyeIdx);
        const rightEye = avg(rightEyeIdx);
        const eyeMid = { x: (leftEye.x + rightEye.x) / 2, y: (leftEye.y + rightEye.y) / 2 };
        const interEye = Math.hypot(rightEye.x - leftEye.x, rightEye.y - leftEye.y) || 1;
        const nose = pts[noseTipIdx];
        const chin = pts[chinIdx];
        const yaw = (nose.x - eyeMid.x) / interEye; // left(-) right(+)
        const pitchRatio = (nose.y - eyeMid.y) / Math.max(1, (chin.y - eyeMid.y)); // up(small) down(large)
        // const rollRad = Math.atan2(rightEye.y - leftEye.y, rightEye.x - leftEye.x);
        // const rollDeg = (rollRad * 180) / Math.PI;

        const YAW_SIDE = 0.18;
        const YAW_WEAK = 0.08;
        const PITCH_UP = 0.45;
        const PITCH_DOWN = 0.65;

        if (Math.abs(yaw) < YAW_WEAK) {
          if (pitchRatio < PITCH_UP) return 'up';
          if (pitchRatio > PITCH_DOWN) return 'down';
          if (!images['frontal1']) return 'frontal1';
          if (!images['frontal2']) return 'frontal2';
          return 'frontal1';
        }
        const side = yaw > 0 ? 'right' : 'left';
        if (Math.abs(yaw) >= YAW_SIDE) {
          if (pitchRatio < PITCH_UP) return `${side}_top`;
          if (pitchRatio > PITCH_DOWN) return `${side}_bottom`;
          return side;
        }
        // weak side turn
        return side;
      } catch (e) {
        return null;
      }
    }

    // Detect face bằng Haar Cascade qua opencv.js
    if (window.cv && window.cv.CascadeClassifier) {
      // Đọc ảnh từ canvas
      const src = window.cv.imread(c);
      const gray = new window.cv.Mat();
      window.cv.cvtColor(src, gray, window.cv.COLOR_RGBA2GRAY, 0);
      const faceCascade = new window.cv.CascadeClassifier();
      // Đường dẫn model haarcascade_frontalface_default.xml
      faceCascade.load('model/haarcascade_frontalface_default.xml');
      const faces = new window.cv.RectVector();
      faceCascade.detectMultiScale(gray, faces, 1.1, 5, 0);
      if (faces.size() === 0) {
        alert('Không phát hiện được khuôn mặt bằng Haar Cascade.');
        src.delete(); gray.delete(); faces.delete(); faceCascade.delete();
        return;
      }
      const face = faces.get(0);
      // Crop khuôn mặt
      const cropped = src.roi(face);
      // Tạo canvas tạm để xuất ảnh (face-only), sau đó bọc padding xám
      const faceCanvas = document.createElement('canvas');
      faceCanvas.width = face.width;
      faceCanvas.height = face.height;
      window.cv.imshow(faceCanvas, cropped);
      const paddedCanvas = createPaddedCanvas(faceCanvas);
      // Detect pose and decorate label accordingly (on padded canvas)
      const detectedKey = await classifyPoseFromCanvas(paddedCanvas);
      const chosenKey = detectedKey && !images[detectedKey] ? detectedKey : POSITIONS[currentIdx].key;
      const posLabel = LABEL_BY_KEY[chosenKey] || POSITIONS[currentIdx].label;
      decorateFaceCanvas(paddedCanvas, posLabel);
      const data = paddedCanvas.toDataURL('image/jpeg', 0.95);
      src.delete(); gray.delete(); faces.delete(); faceCascade.delete(); cropped.delete();
      const pos = chosenKey;
      setImages(prev => {
        const next = { ...prev, [pos]: data };
        const nextIdx = POSITIONS.findIndex(p => !next[p.key]);
        setCurrentIdx(nextIdx >= 0 ? nextIdx : currentIdx);
        return next;
      });
      return;
    }
    // Nếu không có opencv.js, fallback về face-api.js
    const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.2 });
    const detections = await faceapi.detectSingleFace(c, options).withFaceLandmarks();
    if (!detections || !detections.detection) {
      alert('Không phát hiện được khuôn mặt. Vui lòng thử lại!\nHãy đảm bảo mặt rõ, đủ sáng, chiếm phần lớn khung hình.');
      return;
    }
    // Crop theo bounding box khuôn mặt (TinyFaceDetector)
    const box = detections.detection.box;
    const pad = 0;
    const x = Math.max(0, box.x - pad);
    const y = Math.max(0, box.y - pad);
    const w = Math.min(c.width - x, box.width + pad * 2);
    const h = Math.min(c.height - y, box.height + pad * 2);
    const faceCanvas = document.createElement('canvas');
    faceCanvas.width = w;
    faceCanvas.height = h;
    const faceCtx = faceCanvas.getContext('2d')!;
    faceCtx.drawImage(c, x, y, w, h, 0, 0, w, h);
    const paddedCanvas = createPaddedCanvas(faceCanvas);
    // Detect pose and decorate label accordingly
    const detectedKey = await classifyPoseFromCanvas(paddedCanvas);
    const chosenKey = detectedKey && !images[detectedKey] ? detectedKey : POSITIONS[currentIdx].key;
    const posLabel = LABEL_BY_KEY[chosenKey] || POSITIONS[currentIdx].label;
    decorateFaceCanvas(paddedCanvas, posLabel);
    const data = paddedCanvas.toDataURL('image/jpeg', 0.95);

    const pos = chosenKey;
    setImages(prev => {
      const next = { ...prev, [pos]: data };
      const nextIdx = POSITIONS.findIndex(p => !next[p.key]);
      setCurrentIdx(nextIdx >= 0 ? nextIdx : currentIdx);
      return next;
    });
  }

  function startAuto() { setCountdown(3); }

  function retake(posKey: string) {
    const idx = POSITIONS.findIndex(p => p.key === posKey);
    if (idx >= 0) setCurrentIdx(idx);
    setImages(prev => { const n = { ...prev }; delete n[posKey]; return n; });
  }

  function handleUpload(posKey: string, e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string;
      setImages(prev => ({ ...prev, [posKey]: dataUrl }));
    };
    reader.readAsDataURL(file);
  }

  async function mockUpload() {
    const userIdStr = sessionStorage.getItem('userId');
    const userId = userIdStr ? Number(userIdStr) : null;
    if (!userId) { alert('Không xác định userId trong session'); return; }
    if (Object.keys(images).length < POSITIONS.length) { alert('Cần thu thập đủ 10 ảnh'); return; }
    setMockUploading(true);
    try {
      // 1) delete existing faces for user
      await apiFetch(`/faces/${userId}`, { method: 'DELETE' });
      // 2) upload each image
      const keys = POSITIONS.map(p => p.key);
      for (let i = 0; i < keys.length; i++) {
        const k = keys[i];
        const data = images[k];
        if (!data) continue;
        // strip `data:image/...;base64,` prefix if present
        const stripped = data.indexOf('base64,') >= 0 ? data.split('base64,')[1] : data;
        const body = { user_id: userId, image: stripped };
        console.debug('[ImageUpdate] Direct POST /faces body preview', { key: k, length: (stripped || '').length, sample: (stripped || '').slice(0, 32) });

        // Send as multipart/form-data: backend expects an UploadFile (file.file.read())
        try {
          const token = sessionStorage.getItem('authToken');
          // convert base64 string to Blob
          const b64 = stripped;
          const byteChars = atob(b64);
          const byteNumbers = new Array(byteChars.length);
          for (let j = 0; j < byteChars.length; j++) {
            byteNumbers[j] = byteChars.charCodeAt(j);
          }
          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: 'image/jpeg' });

          const fd = new FormData();
          // server expects field name 'image' (UploadFile) and 'user_id' as form field
          fd.append('image', blob, `${userId}_${k}.jpg`);
          fd.append('user_id', String(userId));

          const url = buildUrl('/faces');
          const headers: Record<string, string> = {};
          if (token) headers.Authorization = `Bearer ${token}`;

          console.debug('[ImageUpdate] fetch POST form-data', { url, hasAuth: !!token, fileName: `${userId}_${k}.jpg`, fileSize: blob.size });
          const resp = await fetch(url, { method: 'POST', headers, body: fd });
          const text = await resp.text();
          let parsed: any = text;
          try { parsed = JSON.parse(text); } catch (_) {}
          console.debug('[ImageUpdate] fetch response', { status: resp.status, url, body: parsed });
          if (!resp.ok) {
            throw new Error(`Status ${resp.status} - ${JSON.stringify(parsed)}`);
          }
        } catch (err:any) {
          console.error('[ImageUpdate] direct POST /faces failed for key', k, err);
          throw err;
        }
      }
      alert('Upload ảnh hoàn tất');
    } catch (e:any) {
      console.error('upload faces error', e);
      alert('Lỗi khi upload: ' + (e?.message || e));
    } finally {
      setMockUploading(false);
    }
  }

  return (
    <StaffLayout>
      <h1 style={{ marginBottom: 16 }}>Thu thập ảnh khuôn mặt</h1>
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        <div>
          <div style={{ width: 640, height: 480, background: '#000', borderRadius: 8, overflow: 'hidden' }}>
            <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
          <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
            <button className="btn btn-primary" onClick={() => doCapture()} disabled={!modelLoaded}>Chụp</button>
            <button className="btn btn-ghost" onClick={startAuto} disabled={!modelLoaded}>Auto (3s)</button>
              {!modelLoaded && <div style={{color:'red',marginTop:8}}>Đang tải model nhận diện khuôn mặt...</div>}
            <div style={{ marginLeft: 12 }}>Progress: {Object.keys(images).length}/{POSITIONS.length}</div>
            <button className="btn btn-primary" onClick={mockUpload} disabled={mockUploading || Object.keys(images).length < POSITIONS.length} style={{ marginLeft: 12 }}>{mockUploading ? 'Uploading...' : 'Mock Upload'}</button>
            {countdown !== null && <div style={{ marginLeft: 12, fontWeight: 700 }}>Đếm ngược: {countdown}</div>}
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>

        <div style={{ width: 360 }}>
          <div className="card" style={{ marginBottom: 12 }}>
            <div className="card-body">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <div style={{ fontWeight: 700 }}>Ảnh đã lưu ({existingFaces.length})</div>
                <button className="btn btn-ghost" onClick={loadExistingFaces} disabled={facesLoading}>Làm mới</button>
              </div>
              {facesError && <div style={{ marginBottom: 8 }}><ErrorBanner message={facesError} onRetry={loadExistingFaces} /></div>}
              {facesLoading && <div>Đang tải ảnh...</div>}
              {!facesLoading && existingFaces.length === 0 && <div>Chưa có ảnh lưu cho tài khoản này.</div>}
              {!facesLoading && existingFaces.length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                  {existingFaces.slice(0, 10).map((src, idx) => (
                    <div key={idx} style={{ width: 64, height: 64, borderRadius: 6, overflow: 'hidden', background: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <img src={src} alt={`face-${idx}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <ol style={{ paddingLeft: 12 }}>
            {POSITIONS.map((p, idx) => (
              <li key={p.key} style={{ padding: 8, background: idx === currentIdx ? '#eef' : undefined, marginBottom: 6, borderRadius: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{p.label}</div>
                    <div style={{ fontSize: 12, color: '#666' }}>{images[p.key] ? 'Đã chụp' : (idx < currentIdx ? 'Bỏ qua' : 'Chưa')}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    {images[p.key] && <>
                      <img src={images[p.key]} alt={p.key} style={{ width: 64, height: 64, objectFit: 'cover', borderRadius: 6 }} />
                      <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>
                        {(() => {
                          const img = new window.Image();
                          img.src = images[p.key];
                          if (img.width && img.height) {
                            return `${img.width}x${img.height}`;
                          }
                          return '';
                        })()}
                      </div>
                    </>}
                    <div style={{ marginTop: 6 }}>
                      <button className="btn btn-ghost" onClick={() => retake(p.key)} disabled={!images[p.key]}>Retake</button>
                      <label style={{ marginLeft: 8 }}>
                        <input type="file" accept="image/*" style={{ display: 'none' }} onChange={e => handleUpload(p.key, e)} />
                        <span style={{ cursor: 'pointer', color: '#1976d2', textDecoration: 'underline' }}>Upload</span>
                      </label>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </StaffLayout>
  );
}