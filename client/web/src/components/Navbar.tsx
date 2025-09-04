import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

const Navbar: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/login');
    }
  };

  const handleLogoClick = () => {
    navigate('/dashboard');
  };

  return (
    <nav className="bg-black">
      <div className="max-w-7xl mx-auto px-12 lg:px-16">
        <div className="flex justify-between items-center h-24 ">
          {/* Left - Brand */}
          <div className="flex items-center">
            <h1 
              className="text-4xl font-bold tracking-tight text-white cursor-pointer hover:text-blue-300 transition-colors"
              onClick={handleLogoClick}
            >
              Finora
            </h1>
          </div>
          
          {/* Right - User Info */}
          <div className="flex items-center space-x-8">
            {user && (
              <div className="text-right">
                <p className="text-xl font-medium text-white">Welcome, {user.full_name}</p>
                <p className="text-base text-blue-400 pt-1">GSTIN: {user.gstin}</p>
              </div>
            )}
            <button 
              onClick={handleLogout}
              className="text-white/60 hover:text-white transition-colors p-3 rounded-lg hover:bg-white/10 cursor-pointer"
              title="Logout"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
