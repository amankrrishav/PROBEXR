import { createContext, useContext } from "react";
import { useAuth } from "../hooks/useAuth.js";
import { useTheme } from "../hooks/useTheme.js";
import { useBackendHealth } from "../hooks/useBackendHealth.js";
import { useProviderStatus } from "../hooks/useProviderStatus.js";
import { useSummaryHistory } from "../hooks/useSummaryHistory.js";

const AppContext = createContext(null);

export function AppProvider({ children }) {
    const { dark, toggleTheme } = useTheme();
    const backendHealth = useBackendHealth();
    const auth = useAuth();
    const providerStatus = useProviderStatus();
    const summaryHistory = useSummaryHistory();

    return (
        <AppContext.Provider
            value={{
                dark,
                toggleTheme,
                backendMode: backendHealth.backendMode,
                auth,
                providerStatus,
                summaryHistory,
            }}
        >
            {children}
        </AppContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAppContext() {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error("useAppContext must be used within an AppProvider");
    }
    return context;
}
