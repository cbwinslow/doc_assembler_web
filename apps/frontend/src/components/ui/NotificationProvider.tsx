import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { useNotificationStore } from '../../stores/notificationStore';
import { cn } from '../../utils/cn';

const notificationIcons = {
  success: CheckCircleIcon,
  error: XCircleIcon,
  warning: ExclamationTriangleIcon,
  info: InformationCircleIcon,
};

const notificationColors = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const iconColors = {
  success: 'text-green-400',
  error: 'text-red-400',
  warning: 'text-yellow-400',
  info: 'text-blue-400',
};

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { notifications, removeNotification } = useNotificationStore();

  return (
    <>
      {children}
      
      {/* Notification container */}
      <div className="fixed inset-0 z-50 pointer-events-none">
        <div className="flex flex-col items-end justify-start min-h-screen pt-4 px-4 pb-6 sm:p-6">
          <div className="w-full flex flex-col items-center space-y-4 sm:items-end">
            <AnimatePresence>
              {notifications.map((notification) => {
                const Icon = notificationIcons[notification.type];
                
                return (
                  <motion.div
                    key={notification.id}
                    initial={{ opacity: 0, y: 50, scale: 0.3 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.5, transition: { duration: 0.2 } }}
                    className="pointer-events-auto w-full max-w-sm"
                  >
                    <div
                      className={cn(
                        'rounded-lg border p-4 shadow-lg',
                        notificationColors[notification.type]
                      )}
                    >
                      <div className="flex">
                        <div className="flex-shrink-0">
                          <Icon 
                            className={cn('h-6 w-6', iconColors[notification.type])} 
                            aria-hidden="true" 
                          />
                        </div>
                        
                        <div className="ml-3 w-0 flex-1">
                          <p className="text-sm font-medium">
                            {notification.title}
                          </p>
                          <p className="mt-1 text-sm opacity-90">
                            {notification.message}
                          </p>
                          
                          {notification.actions && notification.actions.length > 0 && (
                            <div className="mt-4 flex space-x-2">
                              {notification.actions.map((action, index) => (
                                <button
                                  key={index}
                                  type="button"
                                  onClick={() => {
                                    action.action();
                                    removeNotification(notification.id);
                                  }}
                                  className="rounded-md text-sm font-medium hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-offset-2"
                                >
                                  {action.label}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                        
                        <div className="ml-4 flex flex-shrink-0">
                          <button
                            type="button"
                            onClick={() => removeNotification(notification.id)}
                            className="inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 hover:opacity-75"
                          >
                            <span className="sr-only">Close</span>
                            <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </>
  );
};

