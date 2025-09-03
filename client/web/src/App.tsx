import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Login from './pages/Login.tsx';
import Register from './pages/Register.tsx';
import Dashboard from './pages/Dashboard.tsx';
import FileUpload from './pages/FileUpload.tsx';
import SmartAnalysis from './pages/SmartAnalysis.tsx';
import FilingDetails from './pages/FilingDetails.tsx';
import FilingReport from './pages/FilingReport.tsx';
import { useAuthStore } from './store/authStore.ts';

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route 
            path="/login" 
            element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} 
          />
          <Route 
            path="/register" 
            element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} 
          />
          <Route 
            path="/dashboard" 
            element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/filing/upload" 
            element={isAuthenticated ? <FileUpload /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/filing/analysis" 
            element={isAuthenticated ? <SmartAnalysis /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/filing/details" 
            element={isAuthenticated ? <FilingDetails /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/filing/report" 
            element={isAuthenticated ? <FilingReport /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/" 
            element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} 
          />
        </Routes>
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;