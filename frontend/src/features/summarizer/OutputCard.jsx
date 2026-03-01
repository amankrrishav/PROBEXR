import TypingSummary from "./TypingSummary";
import ChatView from "./ChatView";
import DocumentActions from "./DocumentActions";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

export default function OutputCard() {
  const { summaryText, documentId, isRestored, streaming, streamingText } = useSummarizerContext();
  return (
    <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">

      <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-6">
        Summary
      </h3>

      <TypingSummary
        text={summaryText}
        instant={isRestored}
        streaming={streaming}
        streamingText={streamingText}
      />

      {documentId && !streaming && (
        <>
          <DocumentActions documentId={documentId} />
          <ChatView documentId={documentId} />
        </>
      )}

    </div>
  );
}