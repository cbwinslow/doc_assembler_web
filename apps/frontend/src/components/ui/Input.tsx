import React from 'react';
import { cn } from '../../utils/cn';
import type { InputProps } from '../../types';

export const Input: React.FC<InputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  disabled = false,
  required = false,
  className,
  ...props
}) => {
  return (
    <div className="w-full">
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
        required={required}
        className={cn(
          // Base styles
          'block w-full rounded-md border-gray-300 shadow-sm transition-colors focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
          // Error styles
          error && 'border-red-300 focus:border-red-500 focus:ring-red-500',
          // Disabled styles
          disabled && 'bg-gray-50 text-gray-500 cursor-not-allowed',
          className
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

