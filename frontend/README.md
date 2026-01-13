# 🎨 API Monitor - Frontend

A sleek, responsive, and interactive dashboard for managing your API monitors.

## 🚀 Technologies

- **React 19:** Functional components with Hooks.
- **Tailwind CSS:** Utility-first CSS framework for rapid UI development.
- **Chart.js:** Data visualization for response time history.
- **Lucide React:** Beautiful, consistent icon set.
- **Axios:** For API communication with custom interceptors.

## ✨ Features

- **Dark Mode:** System-aware theme toggle with persistent storage.
- **Live Dashboard:** Auto-refreshing status cards with "UP", "DOWN", or "PENDING" states.
- **Advanced Details:**
  - Interactive line charts for latency tracking.
  - Paginated incident logs.
  - Dynamic notification settings (Update Slack/Email on the fly).
- **Authentication:** 
  - Persistent login via LocalStorage.
  - **Auto-Logout:** Interceptor automatically redirects to login if the session expires.

## 🛠️ Development

### Scripts
- `npm run dev`: Starts the Vite development server.
- `npm run build`: Generates a production-ready build.
- `npm run lint`: Runs ESLint to check for code quality.

### Layout System
The application uses a centralized `Layout` component to ensure a consistent experience (Navbar, Theme Toggle, Footer) across all private pages.

## 🏃 How to Run

1. **Install Dependencies:**
   ```bash
   npm install
   ```
2. **Start Development Server:**
   ```bash
   npm run dev
   ```
3. **Build for Production:**
   ```bash
   npm run build
   ```
4. **Environment:** The frontend expects the backend to be running on `http://localhost:8000`. You can change this in `src/constants/api.js`.