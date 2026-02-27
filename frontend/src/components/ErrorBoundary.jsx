import React from "react";

export class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("ErrorBoundary caught an error", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="flex h-full min-h-[400px] flex-col items-center justify-center p-6 text-center">
                    <h2 className="mb-2 text-xl font-semibold text-gray-900 dark:text-gray-100">
                        Something went wrong
                    </h2>
                    <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
                        {this.state.error?.message || "An unexpected error occurred."}
                    </p>
                    <button
                        onClick={() => window.location.reload()}
                        className="rounded-full bg-black px-6 py-2 text-sm font-medium text-white transition hover:opacity-90 dark:bg-white dark:text-black"
                    >
                        Reload Page
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}
