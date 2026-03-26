import React, { Component, ErrorInfo, ReactNode } from "react";

interface ErrorBoundaryProps {
    children: ReactNode;
    fallback?: ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error?: Error;
}

/**
 * Error boundary component for gracefully handling errors in DocCardList components.
 * Provides a fallback UI when errors occur during rendering or data processing.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("DocCardList Error Boundary caught an error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            // Custom fallback UI
            if (this.props.fallback) {
                return this.props.fallback;
            }

            // Default fallback UI
            return (
                <div className="alert alert--danger margin-bottom--md">
                    <h4>Failed to load content</h4>
                    <p>
                        There was an error loading the documentation cards. Please try refreshing
                        the page.
                    </p>
                    <details className="margin-top--sm">
                        <summary>Error details</summary>
                        <pre className="margin-top--sm">
                            {this.state.error?.message || "Unknown error occurred"}
                        </pre>
                    </details>
                </div>
            );
        }

        return this.props.children;
    }
}

/**
 * Higher-order component wrapper for adding error boundary to any component
 */
export function withErrorBoundary<P extends object>(
    Component: React.ComponentType<P>,
    fallback?: ReactNode,
) {
    return function WrappedComponent(props: P) {
        return (
            <ErrorBoundary fallback={fallback}>
                <Component {...props} />
            </ErrorBoundary>
        );
    };
}

export default ErrorBoundary;
