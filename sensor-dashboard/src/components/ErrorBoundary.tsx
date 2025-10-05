import React from "react";

type State = { hasError: boolean; error?: Error | null };

// include children in the props type so `this.props.children` is valid
export default class ErrorBoundary extends React.Component<{ children?: React.ReactNode }, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    // optionally log to monitoring
    // console.error("Uncaught error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6">
          <h2 className="text-xl font-bold text-red-600">Something went wrong</h2>
          <pre className="mt-4 text-sm whitespace-pre-wrap">{String(this.state.error)}</pre>
          <p className="mt-4 text-sm text-gray-500">Open DevTools Console for stack trace.</p>
        </div>
      );
    }
    return this.props.children;
  }
}