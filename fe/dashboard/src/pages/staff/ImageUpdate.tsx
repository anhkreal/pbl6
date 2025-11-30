import React, { useEffect, useRef, useState } from 'react';
import * as faceapi from 'face-api.js';
import StaffLayout from '../../layouts/StaffLayout';
import { apiFetch } from '../../api/http';
import { buildUrl } from '../../api/base';

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

export default function ImageUpdate() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [images, setImages] = useState<Record<string, string>>({});
  const [countdown, setCountdown] = useState<number | null>(null);
  const [mockUploading, setMockUploading] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);

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

    // Detect face với tham số nhạy hơn
    const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.2 });
    const detections = await faceapi.detectSingleFace(c, options).withFaceLandmarks();
    if (!detections || !detections.detection) {
      alert('Không phát hiện được khuôn mặt. Vui lòng thử lại!\nHãy đảm bảo mặt rõ, đủ sáng, chiếm phần lớn khung hình.');
      return;
    }
    // Crop theo bounding box khuôn mặt
    const box = detections.detection.box;
    // Tăng padding một chút cho tự nhiên
    const pad = 20;
    const x = Math.max(0, box.x - pad);
    const y = Math.max(0, box.y - pad);
    const w = Math.min(c.width - x, box.width + pad * 2);
    const h = Math.min(c.height - y, box.height + pad * 2);

    // Tạo canvas tạm để crop
    const faceCanvas = document.createElement('canvas');
    faceCanvas.width = w;
    faceCanvas.height = h;
    const faceCtx = faceCanvas.getContext('2d')!;
    faceCtx.drawImage(c, x, y, w, h, 0, 0, w, h);
    const data = faceCanvas.toDataURL('image/jpeg', 0.95);

    const pos = POSITIONS[currentIdx].key;
    setImages(prev => ({ ...prev, [pos]: data }));
    setCurrentIdx(i => Math.min(i + 1, POSITIONS.length - 1));
  }

  function startAuto() { setCountdown(3); }

  function retake(posKey: string) {
    const idx = POSITIONS.findIndex(p => p.key === posKey);
    if (idx >= 0) setCurrentIdx(idx);
    setImages(prev => { const n = { ...prev }; delete n[posKey]; return n; });
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
            <button onClick={() => doCapture()} style={{ padding: '8px 12px' }} disabled={!modelLoaded}>Chụp</button>
            <button onClick={startAuto} style={{ padding: '8px 12px' }} disabled={!modelLoaded}>Auto (3s)</button>
              {!modelLoaded && <div style={{color:'red',marginTop:8}}>Đang tải model nhận diện khuôn mặt...</div>}
            <div style={{ marginLeft: 12 }}>Progress: {Object.keys(images).length}/{POSITIONS.length}</div>
            <button onClick={mockUpload} disabled={mockUploading || Object.keys(images).length < POSITIONS.length} style={{ marginLeft: 12, padding: '8px 12px' }}>{mockUploading ? 'Uploading...' : 'Mock Upload'}</button>
            {countdown !== null && <div style={{ marginLeft: 12, fontWeight: 700 }}>Đếm ngược: {countdown}</div>}
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>

        <div style={{ width: 340 }}>
          <ol style={{ paddingLeft: 12 }}>
            {POSITIONS.map((p, idx) => (
              <li key={p.key} style={{ padding: 8, background: idx === currentIdx ? '#eef' : undefined, marginBottom: 6, borderRadius: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{p.label}</div>
                    <div style={{ fontSize: 12, color: '#666' }}>{images[p.key] ? 'Đã chụp' : (idx < currentIdx ? 'Bỏ qua' : 'Chưa')}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    {images[p.key] && <img src={images[p.key]} alt={p.key} style={{ width: 64, height: 64, objectFit: 'cover', borderRadius: 6 }} />}
                    {images[p.key] && <div><button onClick={() => retake(p.key)} style={{ marginTop: 6 }}>Retake</button></div>}
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