import { AppProviders } from "./app/AppProviders";
import { AppRoutes } from "./app/routes";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { TopBar } from "./components/layout/TopBar";
import { StatusBar } from "./components/layout/StatusBar";

export default function App() {
  return (
    <AppProviders>
      <div className="app-shell">
        <TopBar />
        <div className="app-body">
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
        </div>
        <StatusBar />
      </div>
    </AppProviders>
  );
}
