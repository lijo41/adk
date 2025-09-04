import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { Button } from '../components/ui/Button.tsx';
import { Input } from '../components/ui/Input.tsx';
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

  const navigate = useNavigate();

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-cyan-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-4xl font-bold text-slate-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-lg font-medium text-blue-700">
            GST Filing System
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Email Address"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              placeholder="Enter your email"
            />
            
            <Input
              label="Username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={formData.username}
              onChange={handleChange}
              error={errors.username}
              placeholder="Choose a username"
            />
            
            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              value={formData.password}
              onChange={handleChange}
              error={errors.password}
              placeholder="Create a password"
            />
            
            <Input
              label="Full Name"
              name="full_name"
              type="text"
              autoComplete="name"
              required
              value={formData.full_name}
              onChange={handleChange}
              error={errors.full_name}
              placeholder="Enter your full name"
            />
            
            <Input
              label="Company Name"
              name="company_name"
              type="text"
              autoComplete="organization"
              required
              value={formData.company_name}
              onChange={handleChange}
              error={errors.company_name}
              placeholder="Enter your company name"
            />
            
            <Input
              label="GSTIN"
              name="gstin"
              type="text"
              required
              value={formData.gstin}
              onChange={handleChange}
              error={errors.gstin}
              placeholder="Enter your GSTIN (e.g., 27ABCDE1234F1Z5)"
            />
            
            <Input
              label="Phone Number (Optional)"
              name="phone"
              type="tel"
              autoComplete="tel"
              value={formData.phone}
              onChange={handleChange}
              error={errors.phone}
              placeholder="Enter your phone number"
            />
          </div>

          <div>
            <Button
              type="submit"
              className="w-full"
              loading={loading}
              disabled={loading}
            >
              {loading ? 'Creating account...' : 'Create account'}
            </Button>
          </div>

          <div className="text-center">
            <p className="text-sm text-slate-600">
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-medium text-blue-700 hover:text-blue-800"
              >
                Sign in here
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
