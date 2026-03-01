import { createContext, useContext } from "react";
import { useAuth } from "../hooks/useAuth.js";
import { useTheme } from "../hooks/useTheme.js";
import { useBackendHealth } from "../hooks/useBackendHealth.js";

const AppContext = createContext(null);

export function AppProvider({ children }) {
    const { dark, toggleTheme } = useTheme();
    const backendHealth = useBackendHealth();
    const auth = useAuth();

    return (
        <AppContext.Provider
            value={{
                dark,
                toggleTheme,
                backendMode: backendHealth.backendMode,
                auth,
            }}
        >
            {children}
        </AppContext.Provider>
    );
}

export function useAppContext() {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error("useAppContext must be used within an AppProvider");
    }
    return context;
}
