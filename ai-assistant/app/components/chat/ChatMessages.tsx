import React from 'react';
import MarkdownBlock from './MarkdownBlock';
import { DocumentDuplicateIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

interface ChatMessagesProps {
    messages: Array<{
        text: string;
        isUser: boolean;
        isLoading?: boolean;
        isCited?: boolean;
        rawText?: string;
        citedText?: string | null;
        showCitations?: boolean;
    }>;
    interimTranscript: string;
}

export default function ChatMessages({ messages, interimTranscript }: ChatMessagesProps) {
    const [copiedIndex, setCopiedIndex] = React.useState<number | null>(null);
    const [showCitations, setShowCitations] = React.useState<boolean>(true);

    const copyToClipboard = (text: string, index: number) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        });
    };

    const toggleCitations = () => {
        setShowCitations(!showCitations);
    };

    // Get the content of a message
    const getMessageContent = (msg: { 
        text: string; 
        citedText?: string | null; 
        rawText?: string; 
        isUser: boolean;
        isCited?: boolean;
        isLoading?: boolean;
    }) => {
        // If it's a user message or loading, just return the text
        if (msg.isUser || msg.isLoading) {
            return msg.text;
        }
    
        // For streaming responses (non-final)
        if (!msg.isCited) {
            return msg.text;
        }
    
        // For final responses with citations
        if (msg.isCited) {
            return showCitations && msg.citedText ? msg.citedText : msg.rawText || msg.text;
        }
    
        return msg.text;
    };

    return (
        <div className="h-full flex flex-col">
            <div className="flex-1 overflow-y-auto">
                <div className="p-4 space-y-4">
                    {messages.map((msg, index) => (
                        <div key={index} className={`message-wrapper ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
                            <div className={`message ${msg.isUser ? 'message-user' : 'message-assistant'} ${msg.isLoading ? 'loading' : ''}`}>
                                <MarkdownBlock content={getMessageContent(msg)} />
                                {!msg.isUser && (
                                    <div className="flex flex-row justify-end space-x-2 mt-2">
                                        {msg.isLoading ? (
                                            <div className="flex items-center space-x-2 text-gray-400">
                                                <div className="animate-pulse flex space-x-1">
                                                    <div className="h-1.5 w-1.5 bg-gray-400 rounded-full"></div>
                                                    <div className="h-1.5 w-1.5 bg-gray-400 rounded-full animation-delay-200"></div>
                                                    <div className="h-1.5 w-1.5 bg-gray-400 rounded-full animation-delay-400"></div>
                                                </div>
                                                <span className="text-sm">Thinking...</span>
                                            </div>
                                        ) : msg.isCited && (
                                            <>
                                                {msg.citedText && (
                                                    <button
                                                        onClick={toggleCitations}
                                                        className="citations-button transition-colors duration-400 hover:bg-gray-800 rounded px-2 py-1 text-sm text-gray-300 hover:text-gray-400"
                                                        aria-label="Toggle citations visibility"
                                                    >
                                                        {showCitations ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                                                    </button>
                                                )}
                                                <button
                                                    onClick={() => copyToClipboard(getMessageContent(msg), index)}
                                                    className="copy-button transition-colors duration-400 hover:bg-gray-800 rounded p-1"
                                                    aria-label="Copy model response"
                                                >
                                                    <DocumentDuplicateIcon className={`h-5 w-5 transition-colors duration-300 ${copiedIndex === index ? 'text-green-500' : 'text-gray-300 hover:text-gray-400'}`} />
                                                </button>
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {interimTranscript && (
                        <div className="message-wrapper justify-end">
                            <div className="message message-user interim">{interimTranscript}</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
