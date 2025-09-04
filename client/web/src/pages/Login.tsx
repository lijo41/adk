import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';
import type { UserLogin } from '../types/index.ts';

const Login: React.FC = () => {
  const [formData, setFormData] = useState<UserLogin>({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<UserLogin>>({});
  const [currentWord, setCurrentWord] = useState('');
  const [wordIndex, setWordIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  const navigate = useNavigate();
  const { login } = useAuthStore();

  // Typewriter animation words
  const words = ['Reimagined.', 'Simplified.', 'Automated.', 'Streamlined.'];

  useEffect(() => {
    const typeSpeed = 150;
    const deleteSpeed = 100;
    const pauseTime = 2000;

    const type = () => {
      const currentWordText = words[wordIndex];
      
      if (!isDeleting) {
        // Typing
        if (currentWord.length < currentWordText.length) {
          setCurrentWord(currentWordText.slice(0, currentWord.length + 1));
        } else {
          // Finished typing, pause then start deleting
          setTimeout(() => setIsDeleting(true), pauseTime);
          return;
        }
      } else {
        // Deleting
        if (currentWord.length > 0) {
          setCurrentWord(currentWordText.slice(0, currentWord.length - 1));
        } else {
          // Finished deleting, move to next word
          setIsDeleting(false);
          setWordIndex((prev) => (prev + 1) % words.length);
          return;
        }
      }
    };

    const timer = setTimeout(type, isDeleting ? deleteSpeed : typeSpeed);
    return () => clearTimeout(timer);
  }, [currentWord, wordIndex, isDeleting, words]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev: UserLogin) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof UserLogin]) {
      setErrors((prev: any) => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<UserLogin> = {};

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.login(formData);
      
      // Store token first to enable authenticated requests
      login(response.access_token, null);
      
      // Get user profile with authenticated request
      const userProfile = await authApi.getProfile();
      
      // Update with user data
      login(response.access_token, userProfile);
      
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Login error:', error);
      const errorMessage = error.response?.data?.detail || 'Login failed. Please try again.';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - GSTR1 Information - 60% */}
      <div className="w-3/5 bg-gradient-to-br from-blue-950 via-blue-800 to-slate-900 relative overflow-hidden">
        {/* Subtle gradient overlay for depth */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-blue-900/30"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/40 via-transparent to-slate-800/20"></div>
        
        <div className="relative z-10 flex items-center h-full px-12 lg:px-16">
          <div className="w-full max-w-2xl">
            {/* Brand section */}
            <div className="flex items-center mb-16">
              <div className="w-16 h-16 bg-white/15 backdrop-blur-sm rounded-xl flex items-center justify-center mr-5 border border-white/30">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h1 className="text-white text-4xl font-bold tracking-tight">Finora</h1>
            </div>
            
            {/* Main heading */}
            <div className="mb-14">
              <h2 className="text-white text-5xl font-bold mb-6 leading-tight">
                GST Filing
                <br />
                <span className="bg-gradient-to-r from-blue-300 via-blue-400 to-blue-500 bg-clip-text text-transparent">
                  {currentWord}
                  <span className="text-blue-400 ml-1 font-thin animate-[blink_1s_ease-in-out_infinite]">|</span>
                </span>
              </h2>
              
              <p className="text-white/70 text-xl leading-relaxed font-normal max-w-xl">
                Transform your GST compliance with AI-powered automation. Upload, process, and file with unprecedented ease.
              </p>
            </div>
            
            {/* Features grid */}
            <div className="space-y-6">
              <div className="flex items-center group">
                <div className="w-12 h-12 bg-white/15 backdrop-blur-sm rounded-lg flex items-center justify-center mr-5 group-hover:bg-white/25 transition-all duration-300">
                  <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-medium text-lg">AI-Powered Processing</h3>
                  <p className="text-white/60 text-base">Intelligent document analysis</p>
                </div>
              </div>
              
          
              
              <div className="flex items-center group">
                <div className="w-12 h-12 bg-white/15 backdrop-blur-sm rounded-lg flex items-center justify-center mr-5 group-hover:bg-white/25 transition-all duration-300">
                  <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-medium text-lg">Instant Filing</h3>
                  <p className="text-white/60 text-base">One-click submission</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Right Side - Sign In Form - 40% */}
      <div className="w-2/5 bg-black flex flex-col justify-center px-12 lg:px-16">
        <div className="w-full max-w-sm mx-auto">
          <div className="mb-10">
            <h2 className="text-white text-3xl font-semibold">Sign in to continue</h2>
            <p className="text-gray-400 text-md font-normal mt-2">Enter the account details below.</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-8">
              <div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={formData.username}
                  onChange={handleChange}
                  className="w-full px-0 py-4 bg-transparent border-0 border-b border-gray-600 text-white text-base placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:bg-transparent transition-colors"
                  style={{
                    WebkitBoxShadow: '0 0 0 1000px black inset',
                    WebkitTextFillColor: 'white',
                    caretColor: '#3b82f6'
                  }}
                  placeholder="Email address"
                />
                {errors.username && (
                  <p className="mt-1 text-sm text-red-500">{errors.username}</p>
                )}
              </div>
              
              <div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full px-0 py-4 bg-transparent border-0 border-b border-gray-600 text-white text-base placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:bg-transparent transition-colors"
                  style={{
                    WebkitBoxShadow: '0 0 0 1000px black inset',
                    WebkitTextFillColor: 'white',
                    caretColor: '#3b82f6'
                  }}
                  placeholder="Password"
                />
                {errors.password && (
                  <p className="mt-1 text-sm text-red-500">{errors.password}</p>
                )}
              </div>
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-normal py-3 px-6 text-base transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed mt-8"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
            
            <div className="text-center mt-6">
              <p className="text-gray-400 text-sm font-normal">
                Don't have an account?{' '}
                <Link
                  to="/register"
                  className="text-blue-400 hover:text-blue-300 font-normal"
                >
                  Create account
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
