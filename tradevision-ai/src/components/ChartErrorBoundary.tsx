import React from 'react';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ChartErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Silently recover from "Object is disposed" errors caused by HMR/double-mount
    if (error.message?.includes('disposed')) {
      console.warn('[ChartErrorBoundary] Recovered from chart disposal error. Retrying...');
      setTimeout(() => this.setState({ hasError: false, error: null }), 100);
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.state.error?.message?.includes('disposed')) {
        // Auto-recover: show a brief loading state then retry
        return (
          <div className="flex items-center justify-center h-full min-h-[300px]">
            <div className="flex items-center gap-2 text-[#94A3B8]">
              <div className="w-5 h-5 border-2 border-[#6366F1] border-t-transparent rounded-full animate-spin" />
              <span className="text-sm font-mono">Reinitializing chart engine...</span>
            </div>
          </div>
        );
      }
      return this.props.fallback || (
        <div className="flex items-center justify-center h-full min-h-[300px] text-[#EF4444] text-sm font-mono">
          Chart rendering error. Please refresh.
        </div>
      );
    }
    return this.props.children;
  }
}
