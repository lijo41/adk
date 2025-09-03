import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card.tsx';
import { useAuthStore } from '../store/authStore.ts';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Still navigate to login even if logout fails
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header with Company Info */}
      <div className="border-b bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-foreground">GST Filing Assistant</h1>
              {user && (
                <div className="mt-2 p-4 bg-muted rounded-lg">
                  <p className="text-lg font-medium">Welcome back, {user.company_name}</p>
                  <p className="text-sm text-muted-foreground">GSTIN: {user.gstin}</p>
                </div>
              )}
            </div>
            <Button onClick={handleLogout} variant="outline">
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Main Dashboard Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          
          {/* Start New Filing Card */}
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle>Start New Filing</CardTitle>
              <CardDescription>
                Upload documents and create a new GST filing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                className="w-full" 
                onClick={() => navigate('/filing/upload')}
              >
                Start Filing Wizard
              </Button>
            </CardContent>
          </Card>

          {/* Previous Filings Card */}
          <Card className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center">
                <div className="text-4xl mr-4">📊</div>
                <div>
                  <CardTitle>Previous Filings</CardTitle>
                  <CardDescription>
                    View and manage your filing history
                  </CardDescription>
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
