# Copilot Project Instructions

These instructions guide AI coding agents working in this multi-framework face recognition & emotion analysis workspace.

## Big Picture
- Repository combines face recognition (ArcFace variants: mxnet/torch/paddle/oneflow), partial FC training, reconstruction (3D face, stylegan2), and downstream applications (emotion logs, KPI, staff mgmt) to support a cafe workforce monitoring system.
- Two runtime contexts: (1) Edge (Raspberry Pi) for real-time video capture, face detection, emotion inference; (2) Server (laptop) for identity resolution (`/query`), log aggregation, admin/staff web dashboards.
- Model zoo & backbones live under `insightface/python-package/insightface` and `recognition/*` frameworks; avoid cross-contaminating changes between framework implementations.

## Key Code Areas
- Face detection & recognition: `recognition/arcface_*` (framework-specific) + `partial_fc/` for distributed class center management.
- 3D/reconstruction & augmentation: `reconstruction/ostec/external/` (stylegan2, landmark, segmentation) & `thirdparty/face3d`.
- Utility scripts: search under `tools/`, e.g., model conversion `tools/onnx2caffe`.
- Data assets: `python-package/insightface/data/` (images, objects) used for tests/examples—do not commit large new binaries here.

## Conventions
- Multiple deep learning frameworks coexist; keep implementation parity when updating core logic (e.g., backbone hyperparams) across `arcface_*` directories.
- Training/eval scripts separated by framework: prefer adding new experiments under the matching framework folder (`scripts/`, `eval/`, `configs/`).
- PIN-protected admin actions (delete/reset/update) should route through a dedicated verification endpoint rather than overloading generic CRUD.
- Logs (emotion, checkin/out, KPI) should be append-only storage with server-side filtering & pagination (limit 30 rows UI constraint).

## Planned Frontends (to scaffold)
- Edge Stream Web (RPI): Lightweight Flask or FastAPI endpoint exposing MJPEG/WebSocket with per-frame overlays (bounding box, identity from `/query`, local emotion inference) and POSTing emotion logs to server.
- Management Dashboard (Laptop): React + TypeScript app with role-based routing (admin vs staff) and modular pages: Dashboard, EmotionLog, CheckInOut, KPI Report, Employee Management, Profile, Image Update, Contact.

## API Contracts (Server)
- Auth: `POST /auth/login {username,password}` -> tokens; role in response.
- Identity: `POST /query {embedding}` -> `{id,name}`.
- Emotion Log ingest: `POST /emotions {staffId, timestamp, emotion, frameImage}`.
- Emotion Log query: `GET /emotions?from=&to=&staffName=&limit=30&negativeOnly=1`.
- Checkin/out: `POST /attendance/checkin {staffId}` / `POST /attendance/checkout {staffId}`; query `GET /attendance?date=&staffName=`.
- KPI: `GET /kpi?mode=day|month&date=YYYY-MM-DD|YYYY-MM&staffName=`.
- Employees CRUD: `GET /employees`, `POST /employees`, `PATCH /employees/{id}`, `POST /employees/{id}/shift`, `POST /employees/{id}/reset`, `DELETE /employees/{id}`.
- PIN verify: `POST /admin/verify-pin {pin}` returns 200/403.

## Implementation Notes
- Emotion KPI score = weighted combination (define constant table) of positive vs negative ratios + attendance; centralize formula in one module and reuse for KPI report & per-employee detail.
- Limit heavy model loads to initialization; reuse global singleton for detection/embedding models on edge and server.
- Use pagination & projection—never send raw embeddings or large images in list responses.
- RPI should batch emotion log POSTs (e.g., every N seconds) to reduce network overhead.

## Safe Changes
- When modifying backbone architectures, replicate across all framework flavors & adjust configs.
- Add new endpoints in a dedicated service layer; do not call model code directly from route handlers—introduce a manager/controller.
- Prefer extending partial FC logic rather than replacing to keep compatibility with existing training pipelines.

## Testing & Validation
- For new API endpoints: add minimal integration test (auth + one happy path + one auth failure).
- For model changes: run evaluation scripts under respective `eval/` folders (e.g., IJB, MegaFace) before merging.

## Performance Considerations
- Keep per-request inference < ~100ms for identity query; precompute normalized embeddings.
- Use async streaming for video; avoid blocking CPU with image encoding on main thread.

## What Not To Do
- Don’t unify frameworks prematurely; maintain separate namespace boundaries.
- Don’t store raw video or full resolution frames in logs—thumbnail or base64 small images only.
- Don’t hardcode PINs or credentials; expect environment variables.

## Quick Start (to be added)
- Edge: init models, start stream server, confirm boxes + identity overlay.
- Dashboard: install dependencies, run dev server, login as admin/staff.

Feedback welcome: Clarify any unclear API, data flow, or add missing conventions.