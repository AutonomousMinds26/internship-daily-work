# RecruiterAI — Frontend Client

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Railway-0B0D0E?style=flat&logo=railway)](https://recruiterai-frontend-production.up.railway.app/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript)]()
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite)]()

The single-page web interface for **RecruiterAI**, an autonomous AI-driven Applicant Tracking System (ATS) and talent intelligence portal.

---

## 🌐 Live Production Demo

- **URL**: [https://recruiterai-frontend-production.up.railway.app/](https://recruiterai-frontend-production.up.railway.app/)
- **Default Accounts**:
  - **Admin**: `admin_user` / `admin_password`
  - **Recruiter**: `recruiter_user` / `recruiter_password`

---

## ✨ Features

- 📋 **Kanban Pipeline Board**: Drag-and-drop / stage transition candidate workflows (Applied, Sourced, Screening, Assessment, Interview, Offer, Hired, Rejected).
- 📊 **Candidate Deep-Dive**: 11-point weighted scoring breakdown, ATS keyword analysis, skill gap highlights, and AI-generated executive summaries.
- 🧪 **Sandboxed Code Assessments**: Multi-language technical assessment triggers with live scoring and test case reports.
- 🛡️ **Admin Console**: Enterprise RBAC management, audit log inspection, and real-time backend microservice health status.
- 📡 **Real-time Team Collaboration**: Live candidate updates powered by WebSocket broadcast service.
- 🔒 **Privacy & DSAR Center**: GDPR & DPDP compliant candidate data export and right-to-erasure workflows.
- 📈 **Predictive Analytics & Diversity**: 4/5ths adverse impact calculations and hiring velocity forecasting.

---

## 🛠️ Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS & Lucide Icons
- **HTTP Client**: Axios with JWT interceptors
- **Real-time**: WebSockets

---

## 🚀 Getting Started

### Local Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment** (optional):
   Create a `.env` or `.env.local` file:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

3. **Run local dev server**:
   ```bash
   npm run dev
   ```
   Access the app at `http://localhost:5173`.

### Production Build

```bash
npm run build
npm run preview
```

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/       # UI Components (Kanban, CandidateModal, AdminConsole, etc.)
│   ├── services/         # API clients (api.ts, adminService.ts, offerService.ts, websocketService.ts)
│   ├── types/            # TypeScript interfaces & domain models
│   ├── App.tsx           # Main application state & routing
│   └── main.tsx          # Application entrypoint
├── public/               # Static assets & favicon
├── Dockerfile            # Multi-stage production Nginx container
├── package.json          # Dependencies & scripts
└── vite.config.ts        # Vite configuration
```
