# Project Overview

This project is a full-stack application consisting of a Python backend and a React (TypeScript) frontend.

## Backend

The backend is built with **FastAPI** and handles audio processing, real-time data from a Presage device, and triage output using the `google-genai` library.

**Key Technologies:**
*   **FastAPI:** Web framework for building APIs.
*   **Uvicorn:** ASGI server for running FastAPI applications.
*   **Pydantic:** Data validation and settings management.
*   **NumPy, SciPy, Librosa:** Likely used for audio feature computation.
*   **Websockets:** For real-time communication.
*   **Google GenAI:** For generative AI capabilities, possibly for triage output or analysis.

**Dependencies (from `backend/requirements.txt`):**
*   `fastapi`
*   `uvicorn`
*   `websockets`
*   `pydantic`
*   `numpy`
*   `scipy`
*   `librosa`
*   `python-dotenv`
*   `google-genai`

**Running the Backend:**

1.  Navigate to the project root directory.
2.  Activate the Python virtual environment (if not already active): `source venv/bin/activate`
3.  Install dependencies: `pip install -r backend/requirements.txt`
4.  Run the FastAPI application (assuming `backend/main.py` is the entry point):
    ```bash
    uvicorn backend.main:app --reload
    ```
    The `--reload` flag enables live-reloading during development.

## Frontend

The frontend is a **React** application built with **TypeScript** and **Vite**. It provides the user interface for interacting with the backend, displaying camera output, and other relevant information.

**Key Technologies:**
*   **React:** JavaScript library for building user interfaces.
*   **TypeScript:** Typed superset of JavaScript.
*   **Vite:** Fast frontend build tool.

**Dependencies (from `frontend/package.json`):**
*   `react`
*   `react-dom`

**Development Dependencies:**
*   `@types/react`
*   `@types/react-dom`
*   `@vitejs/plugin-react`
*   `typescript`
*   `vite`

**Running the Frontend:**

1.  Navigate to the `frontend` directory: `cd frontend`
2.  Install dependencies: `npm install` (or `yarn install` if using yarn)
3.  Start the development server: `npm run dev` (or `yarn dev`)
    This will typically open the application in your browser at `http://localhost:5173` (or a similar port).

**Building the Frontend:**

1.  Navigate to the `frontend` directory: `cd frontend`
2.  Build the production-ready assets: `npm run build` (or `yarn build`)

## Native Presage Bridge (`bridge/`)

This directory is intended for a **native C++ application** that integrates directly with the **Presage SmartSpectra SDK**. Its primary role is to:

*   Access the local webcam (or video source).
*   Process video frames using the Presage SDK to extract vital signs (heart rate, breathing rate, quality) and facial landmark points.
*   Format this processed data into `PresagePacket`s (JSON format).
*   Send these `PresagePacket`s via a WebSocket connection to the Python backend's `/presage_stream` endpoint (e.g., `ws://localhost:8000/presage_stream`).

**Key Point:** The Presage SDK does not run in the browser. This native bridge is a mandatory component for obtaining live Presage data.

## Development Conventions

*   **Backend:** Python code should follow standard Python conventions (e.g., PEP 8). Pydantic is used for data modeling and validation.
*   **Frontend:** TypeScript and React best practices should be followed.
*   **Testing:** (TODO: Add details on testing procedures for both backend and frontend.)
*   **Linting:** (TODO: Add details on linting configurations and commands.)