# Inclusive Education Monitoring Platform

This is a digital platform for monitoring inclusive education programs across India. The application features a comprehensive dashboard for administrators and teachers to track school facilities, student attendance, dropout risks, and overall program effectiveness.

## Tech Stack

### Frontend
- **Framework:** React 18 with Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router
- **Icons:** Lucide React
- **Charts:** Recharts

### Backend
- **Framework:** FastAPI (Python)
- **Database ORM:** SQLAlchemy
- **Authentication:** JWT with role-based access control (RBAC)
- **Data Validation:** Pydantic
- **AI/ML Integration:** Dropout risk prediction and Natural Language querying

## Features

- **Role-Based Access Control:** Distinct roles for National Admins, State Admins, Teachers, and Students.
- **School & Facility Management:** Track accessibility features like ramps, assistive tech, and special educators.
- **Student Monitoring:** Record attendance, academic scores, and predict dropout risks using AI/Heuristic models.
- **Data Ingestion:** Bulk upload capabilities for CSV and JSON data formats.
- **AI-Powered Querying:** Natural language queries to interact with platform data and gain insights.
- **Interactive Dashboards:** Visualizations for attendance trends, facility distributions, and risk assessments.

## Getting Started

### Prerequisites
- Node.js
- Python 3.8+

### Setup Instructions

#### 1. Backend Setup
1. Navigate to the `api` directory (or use the root if it's a unified workspace).
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn api.main:app --reload
   ```

#### 2. Frontend Setup
1. Install Node modules from the root directory:
   ```bash
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```

The frontend will typically run on `http://localhost:5173` and the backend on `http://localhost:8000`.

## Project Structure
- `api/` - FastAPI backend application code
- `src/` - React frontend source code
- `frontend/` - Additional frontend assets/configurations
- `requirements.txt` - Python backend dependencies
- `package.json` - Node.js frontend dependencies
