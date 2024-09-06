import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import CodeBlock from './CodeBlock';
import './ChatInterface.css';
import '../markdown-styles.css';
import { DocumentDuplicateIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';

// Define the ChatInterfaceProps interface
interface ChatInterfaceProps {
    messages: Array<{ text: string; isUser: boolean }>;
    onNewMessage: (message: string) => Promise<void>;
    interimTranscript: string;
    inputMessage: string;  // Add this new prop
    setInputMessage: React.Dispatch<React.SetStateAction<string>>;  // Add this new prop
}

export default function ChatInterface({ messages, onNewMessage, interimTranscript, inputMessage, setInputMessage }: ChatInterfaceProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, interimTranscript]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (inputMessage.trim()) {
            setIsLoading(true);
            await onNewMessage(inputMessage);
            setInputMessage('');
            setIsLoading(false);
        }
    };

    const copyToClipboard = (text: string, index: number) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        });
    };

    return (
        <div className="chat-container">
            <div className="chat-box">
                <div className="chat-messages">
                    {messages.map((msg, index) => (
                        <div key={index} className={`message-wrapper ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
                            <div className={`message ${msg.isUser ? 'message-user' : 'message-ai'}`}>
                                {msg.isUser ? (
                                    <p>{msg.text}</p>
                                ) : msg.text ? (
                                    <>
                                        <ReactMarkdown
                                            className="markdown-content"
                                            components={{
                                                code({ node, className, children, ...props }) {
                                                    const match = /language-(\w+)/.exec(className || '');
                                                    return match ? (
                                                        <CodeBlock
                                                            value={String(children).replace(/\n$/, '')}
                                                            language={match[1]}
                                                        />
                                                    ) : (
                                                        <code className={className} {...props}>
                                                            {children}
                                                        </code>
                                                    );
                                                }
                                            }}
                                        >
                                            {msg.text}
                                        </ReactMarkdown>
                                        <button
                                            onClick={() => copyToClipboard(msg.text, index)}
                                            className="copy-button"
                                            aria-label="Copy model response"
                                        >
                                            <DocumentDuplicateIcon className={`h-5 w-5 ${copiedIndex === index ? 'text-green-500' : 'text-white'}`} />
                                        </button>
                                    </>
                                ) : (
                                    <div className="flex items-center">
                                        <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Thinking...
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
                    <div ref={messagesEndRef} />
                </div>
                <form onSubmit={handleSubmit} className="input-form">
                    <div className="input-container">
                        <input
                            type="text"
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            placeholder="Type a message..."
                            className="chat-input"
                        />
                        <button 
                            type="submit" 
                            className="send-button flex flex-row"
                            disabled={isLoading}
                        >
                            <PaperAirplaneIcon className ="h-6 w-6 pr-2" /> Send
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}