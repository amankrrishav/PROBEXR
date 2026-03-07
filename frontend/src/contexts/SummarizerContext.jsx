import { createContext, useContext } from "react";
import { useSummarizer } from "../hooks/useSummarizer.js";

const SummarizerContext = createContext(null);

export function SummarizerProvider({ children }) {
    const summarizer = useSummarizer();

    return (
        <SummarizerContext.Provider value={summarizer}>
            {children}
        </SummarizerContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSummarizerContext() {
    const context = useContext(SummarizerContext);
    if (!context) {
        throw new Error("useSummarizerContext must be used within a SummarizerProvider");
    }
    return context;
}
