import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

// without this a render error unmounts the whole tree and leaves a blank
// dark page. catching it keeps the failure visible and recoverable.
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("ui error:", error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="page">
          <div className="page-inner">
            <h2>Something went wrong</h2>
            <p style={{ color: "var(--muted)" }}>
              The interface hit an error and stopped rendering.
            </p>
            <pre className="error-message">{this.state.error.message}</pre>
            <button type="button" onClick={() => window.location.reload()}>
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
