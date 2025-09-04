import React from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const handleTryIt = () => {
    navigate('/filing/upload');
  };

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Hero Section with Login Page Background */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-950 via-blue-800 to-slate-900">
        {/* Subtle gradient overlay for depth - same as login */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-blue-900/30"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/40 via-transparent to-slate-800/20"></div>
        
        
        <div className="relative z-10 flex items-center justify-between mr-25 h-full px-12 lg:px-16 py-48">
          <div className="w-full max-w-2xl ml-15">
            {/* Main heading */}
            <div className="mb-14 ">
              <h2 className="text-white text-4xl font-bold mb-6 leading-tight">
                Streamline GST Filing,
                <br />
                <span className="bg-gradient-to-r from-blue-300 via-blue-400 to-blue-500 bg-clip-text text-transparent">
                  Powered by Finora
                </span>
              </h2>
              
              <p className="text-white/70 text-lg leading-relaxed font-normal max-w-xl">
                Transform your GST compliance with AI-powered automation. Upload, process, and file with unprecedented ease.
              </p>
            </div>
            
            <button 
              onClick={handleTryIt}
              className="px-8 py-4 text-lg font-semibold text-white bg-black rounded-lg transition-all duration-300 hover:bg-gray-900 hover:transform hover:scale-105 shadow-lg cursor-pointer"
            >
              TRY IT FREE
            </button>
          </div>

          {/* Enhanced AI Robot Illustration   */}
          <div className="flex justify-center">
            <div className="relative">
              {/* Main Robot Container */}
              <div className="w-74 h-70 bg-white/10 backdrop-blur-sm border border-white/20 rounded-3xl flex items-center justify-center relative overflow-hidden">
                {/* Glass shine effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent" style={{
                  animation: 'shine 4s ease-in-out infinite'
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
                
                {/* Robot Body */}
                <div className="relative z-10">
                  <svg className="w-40 h-40 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
              
              {/* Floating Feature Icons */}
              <div className="absolute -top-6 -left-12 w-16 h-16 bg-black/40 backdrop-blur-sm rounded-xl flex items-center justify-center animate-bounce" style={{animationDelay: '0s', animationDuration: '3s'}}>
                <svg className="w-8 h-8 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              
              <div className="absolute -top-6 -right-12 w-16 h-16 bg-black/40 backdrop-blur-sm rounded-xl flex items-center justify-center animate-bounce" style={{animationDelay: '1s', animationDuration: '3s'}}>
                <svg className="w-8 h-8 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              
              <div className="absolute -bottom-6 -left-12 w-16 h-16 bg-black/40 backdrop-blur-sm  rounded-xl flex items-center justify-center animate-bounce" style={{animationDelay: '2s', animationDuration: '3s'}}>
                <svg className="w-8 h-8 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              
              <div className="absolute -bottom-6 -right-12 w-16 h-16 bg-black/40 backdrop-blur-sm rounded-xl flex items-center justify-center animate-bounce" style={{animationDelay: '0.5s', animationDuration: '3s'}}>
                <svg className="w-8 h-8 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Workflow Section */}
      <div className="py-16 bg-black">
        <div className="max-w-7xl mx-auto px-12 lg:px-16">
          <div className="mb-12">
            <h2 className="text-white text-4xl font-bold leading-tight text-center">
              Simplifying Your GST Workflow from Start to Finish
            </h2>
          </div>

          <div className="space-y-16">
            {/* Step 1: Document Processing */}
            <div className="flex items-center justify-between">
              <div className="flex-1 pr-12">
                <div className="flex items-center mb-4">
                  <div className="w-10 h-10 bg-gray-800 text-white rounded-lg flex items-center justify-center font-bold mr-4 text-base">
                    1
                  </div>
                  <h3 className="text-white font-medium text-xl">Document Processing</h3>
                </div>
                <p className="text-white/70 text-lg leading-relaxed font-normal   ">
                  Our Smart AI automatically identifies and processes your GST documents. 
                  Upload invoices, receipts, and other documents for instant analysis.
                </p>
              </div>
              <div className="flex-1 flex justify-center">
                <div className="w-64 h-48 bg-blue-500/10 backdrop-blur-sm border border-blue-400/30 rounded-lg flex items-center justify-center relative overflow-hidden">
                  {/* Glassmorphism shine effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-300/20 to-transparent animate-pulse" style={{
                    animation: 'shine 3s ease-in-out infinite'
                  }}></div>
                  
                  {/* Document stack with blue theme */}
                  <div className="relative z-10">
                    <div className="absolute -rotate-12 w-12 h-16 bg-blue-400/40 backdrop-blur-sm rounded-sm border border-blue-300/50 shadow-lg"></div>
                    <div className="absolute rotate-6 w-12 h-16 bg-blue-500/50 backdrop-blur-sm rounded-sm border border-blue-400/60 translate-x-2 shadow-lg"></div>
                    <div className="w-12 h-16 bg-blue-600/60 backdrop-blur-sm rounded-sm border border-blue-500/70 translate-x-4 relative z-10 shadow-lg">
                      <div className="w-full h-0.5 bg-blue-200/60 mt-2 rounded-full"></div>
                      <div className="w-3/4 h-0.5 bg-blue-200/50 mt-1 rounded-full"></div>
                      <div className="w-full h-0.5 bg-blue-200/60 mt-1 rounded-full"></div>
                      <div className="w-2/3 h-0.5 bg-blue-200/50 mt-1 rounded-full"></div>
                    </div>
                  </div>
                  
                  {/* Animated upload indicator */}
                  <div className="absolute top-4 right-4">
                    <div className="w-3 h-3 bg-blue-400 rounded-full animate-ping"></div>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                View Filing History
              </Button>
            </CardContent>
          </Card>

        </div>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Your latest GST filing activities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  <div>
                    <div className="font-medium">GSTR1 - March 2024</div>
                    <div className="text-sm text-muted-foreground">Filed successfully</div>
                  </div>
                </div>
                <div className="text-sm text-green-600 font-medium">Completed</div>
              </div>
              
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-3"></div>
                  <div>
                    <div className="font-medium">GSTR2 - March 2024</div>
                    <div className="text-sm text-muted-foreground">Processing documents</div>
                  </div>
                </div>
                <div className="text-sm text-yellow-600 font-medium">In Progress</div>
              </div>
              
              <div className="text-center py-4 text-muted-foreground">
                <Button variant="ghost" onClick={() => navigate('/filing/upload')}>
                  Start your first filing →
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
