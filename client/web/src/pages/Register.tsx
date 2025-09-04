import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { authApi } from '../api/auth.ts';
import type { UserRegistration } from '../types/index.ts';

const Register: React.FC = () => {
  const [formData, setFormData] = useState<UserRegistration & { confirmPassword: string }>({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: '',
    company_name: '',
    gstin: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<UserRegistration & { confirmPassword: string }>>({});
  const [currentWord, setCurrentWord] = useState('');
  const [wordIndex, setWordIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  const navigate = useNavigate();

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
    setFormData((prev: UserRegistration & { confirmPassword: string }) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof (UserRegistration & { confirmPassword: string })]) {
      setErrors((prev: any) => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<UserRegistration & { confirmPassword: string }> = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }


    if (formData.full_name && formData.full_name.trim().length < 2) {
      newErrors.full_name = 'Full name must be at least 2 characters';
    }

    if (!formData.company_name.trim()) {
      newErrors.company_name = 'Company name is required';
    }

    if (!formData.gstin.trim()) {
      newErrors.gstin = 'GSTIN is required';
    } else if (!/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/.test(formData.gstin)) {
      newErrors.gstin = 'Invalid GSTIN format';
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
      const { confirmPassword, ...registrationData } = formData;
      await authApi.register(registrationData);
      toast.success('Registration successful! Please login.');
      navigate('/login');
    } catch (error: any) {
      console.error('Registration error:', error);
      const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - GSTR1 Information - 60% */}
      <div className="w-4/5 bg-gradient-to-br from-blue-950 via-blue-800 to-slate-900 relative overflow-hidden">
        {/* Subtle gradient overlay for depth */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-blue-900/30"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/40 via-transparent to-slate-800/20"></div>
        
        <div className="relative z-10 flex items-center h-full px-12 lg:px-16">
          <div className="w-full max-w-2xl">
            {/* Brand section */}
            <div className="flex items-center mb-16">
              <div className="w-16 h-16 bg-white/15 backdrop-blur-sm rounded-xl flex items-center justify-center mr-5 border border-white/30 relative overflow-hidden group">
                {/* Glass shine effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent" style={{
                  animation: 'shine 3s ease-in-out infinite'
                }}></div>
                <style dangerouslySetInnerHTML={{
                  __html: `
                    @keyframes shine {
                      0% { transform: translateX(-100%); }
                      50% { transform: translateX(100%); }
                      100% { transform: translateX(-100%); }
                    }
                  `
                }} />
                <svg className="w-8 h-8 text-white relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
      
      {/* Right Side - Registration Form - 40% */}
      <div className="w-2/5 bg-black flex flex-col justify-center px-12 lg:px-16">
        <div className="w-full max-w-lg mx-auto">
          <div className="mb-10">
            <h2 className="text-white text-3xl font-semibold">Create your account</h2>
            <p className="text-gray-400 text-base mt-2">Join the future of GST filing</p>
          </div>
        
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-6">
              {/* Row 1: Email (Full Width) */}
              <div>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="Email address"
                  required
                  className="w-full bg-transparent border-0 border-b border-gray-600 text-white placeholder-gray-400 py-3 px-0 focus:outline-none focus:border-blue-400 focus:ring-0 caret-blue-400"
                />
                {errors.email && <p className="text-red-400 text-sm mt-1">{errors.email}</p>}
              </div>

              {/* Row 2: Username and Password */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    placeholder="Username"
                    required
                    className="w-full bg-transparent border-0 border-b border-gray-600 text-white placeholder-gray-400 py-3 px-0 focus:outline-none focus:border-blue-400 focus:ring-0 caret-blue-400"
                  />
                  {errors.username && <p className="text-red-400 text-sm mt-1">{errors.username}</p>}
                </div>
                <div>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    placeholder="Password"
                    required
                    className="w-full bg-transparent border-0 border-b border-gray-600 text-white placeholder-gray-400 py-3 px-0 focus:outline-none focus:border-blue-400 focus:ring-0 caret-blue-400"
                  />
                  {errors.password && <p className="text-red-400 text-sm mt-1">{errors.password}</p>}
                </div>
              </div>

              {/* Row 3: Full Name (Full Width) */}
              <div>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  placeholder="Full Name"
                  required
                  className="w-full bg-transparent border-0 border-b border-gray-600 text-white placeholder-gray-400 py-3 px-0 focus:outline-none focus:border-blue-400 focus:ring-0 caret-blue-400"
                />
                {errors.full_name && <p className="text-red-400 text-sm mt-1">{errors.full_name}</p>}
              </div>

              {/* Row 4: Company Name and GSTIN */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                    placeholder="Company Name"
                    required
                    className="w-full bg-transparent border-0 border-b border-gray-600 text-white placeholder-gray-400 py-3 px-0 focus:outline-none focus:border-blue-400 focus:ring-0 caret-blue-400"
                  />
                  {errors.company_name && <p className="text-red-400 text-sm mt-1">{errors.company_name}</p>}
                </div>
                <div>
                  <input
                    type="text"
                    value={formData.gstin}
                    onChange={(e) => setFormData({...formData, gstin: e.target.value})}
                    placeholder="GSTIN"
                    required
                    className="w-full bg-transparent border-0 border-b border-gray-600 text-white placeholder-gray-400 py-3 px-0 focus:outline-none focus:border-blue-400 focus:ring-0 caret-blue-400"
                  />
                  {errors.gstin && <p className="text-red-400 text-sm mt-1">{errors.gstin}</p>}
                </div>
              </div>

              {/* Row 5: Phone Number (Full Width) */}
              <div>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  placeholder="Phone Number (optional)"
                  className="w-full bg-transparent border-0 border-b border-gray-600 text-white placeholder-gray-400 py-3 px-0 focus:outline-none focus:border-blue-400 focus:ring-0 caret-blue-400"
                />
                {errors.phone && <p className="text-red-400 text-sm mt-1">{errors.phone}</p>}
              </div>

            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 text-base transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed mt-8"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>

            <div className="text-center mt-6">
              <p className="text-gray-400 text-sm">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
                >
                  Sign in here
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Register;
