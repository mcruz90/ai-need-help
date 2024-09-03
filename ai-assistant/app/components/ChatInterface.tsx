import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import CodeBlock from './CodeBlock';
import './ChatInterface.css';

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
                        <div key={index} className={`message ${msg.isUser ? 'message-user' : 'message-ai'}`}>
                            <div className="message-content">
                                {msg.isUser ? (
                                    <p>{msg.text}</p>
                                ) : (
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
                                )}
                            </div>
                            {!msg.isUser && (
                                <div className="text-right">
                                    <button
                                        onClick={() => copyToClipboard(msg.text, index)}
                                        className="copy-button"
                                    >
                                        {copiedIndex === index ? 'Copied!' : 'Copy model response'}
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                    {interimTranscript && (
                        <div className="message message-user">
                            <div className="message-content">
                                {interimTranscript}
                            </div>
                        </div>
                    )}
                    {isLoading && (
                        <div className="text-left">
                            <span className="inline-block p-2 rounded-lg bg-gray-200 text-gray-800">
                                <span className="animate-pulse-custom">...</span>
                            </span>
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
                            className="send-button"
                            disabled={isLoading}
                        >
                            Send
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}