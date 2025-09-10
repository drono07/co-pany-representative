import React from 'react';
import { CheckCircle, AlertTriangle, Clock, Activity } from 'lucide-react';

const StatusIndicator = ({ status, isActive = false, size = 'sm' }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'completed':
        return {
          icon: CheckCircle,
          color: 'text-green-500',
          bgColor: 'bg-green-100',
          text: 'Completed'
        };
      case 'failed':
        return {
          icon: AlertTriangle,
          color: 'text-red-500',
          bgColor: 'bg-red-100',
          text: 'Failed'
        };
      case 'running':
        return {
          icon: Activity,
          color: 'text-blue-500',
          bgColor: 'bg-blue-100',
          text: 'Running'
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100',
          text: 'Pending'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6'
  };

  return (
    <div className="flex items-center space-x-2">
      <div className="relative">
        <Icon className={`${sizeClasses[size]} ${config.color}`} />
        {isActive && status === 'running' && (
          <div className="absolute inset-0">
            <div className="animate-ping">
              <Icon className={`${sizeClasses[size]} ${config.color} opacity-75`} />
            </div>
          </div>
        )}
      </div>
      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${config.bgColor} ${config.color}`}>
        {config.text}
      </span>
      {isActive && (
        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
      )}
    </div>
  );
};

export default StatusIndicator;
