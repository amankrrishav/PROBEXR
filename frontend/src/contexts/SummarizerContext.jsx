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

export function useSummarizerContext() {
    const context = useContext(SummarizerContext);
    if (!context) {
        throw new Error("useSummarizerContext must be used within a SummarizerProvider");
    }
    return context;
}
