import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown, { Components } from 'react-markdown'; 
import CodeBlock from '../codeblock/CodeBlock';
import PastConversations from '../pastconversations/PastConversations';
import './ChatInterface.css';
import '../../markdown-styles.css';
import { DocumentDuplicateIcon, PaperAirplaneIcon, MicrophoneIcon } from '@heroicons/react/24/outline';
import { API_URL } from '../../utils/api';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';

interface MarkdownWithHTMLProps {
    content: string;
    components?: Components;
}

interface CodeComponentProps {
    node?: any; 
    inline?: boolean; 
    className?: string;
    children?: React.ReactNode;
    [key: string]: any; // For additional props
}

// Create a React component to render sanitized HTML with ReactMarkdown
function MarkdownWithHTML({ content }: MarkdownWithHTMLProps) {
    return (
        <ReactMarkdown
            className="markdown-content prose prose-sm sm:prose lg:prose-lg xl:prose-xl"
            rehypePlugins={[rehypeRaw, rehypeSanitize]}
            components={{
                code({
                    node,
                    inline,
                    className,
                    children,
                    ...props
                }: CodeComponentProps) { 
                    const match = /language-(\w+)/.exec(className || '');
                    const language = match ? match[1] : '';
                    const codeString = String(children).replace(/\n$/, '');
                    
                    if (!inline) {
                        return (
                            <CodeBlock
                                value={codeString}
                                language={language || 'text'}
                            />
                        );
                    }
                    
                    return (
                        <code className={`bg-gray-700 text-white px-1 py-0.5 rounded ${className}`} {...props}>
                            {children}
                        </code>
                    );
                },
                a({ node, ...props }) {
                    return (
                        <a {...props} target="_blank" rel="noopener noreferrer">
                            {props.children}
                        </a>
                    );
                },
                sup({ node, ...props }) {
                    return <sup className="inline">{props.children}</sup>;
                },
                blockquote({ node, ...props }) {
                    return <blockquote className="border-l-4 border-gray-300 pl-4 italic" {...props} />;
                },
            }}
        >
            {content}
        </ReactMarkdown>
    );
}

// Define the ChatInterfaceProps interface 
interface ChatInterfaceProps {
    messages: Array<{ text: string; isUser: boolean; isLoading?: boolean }>;
    onNewMessage: (message: string) => Promise<void>;
    interimTranscript: string;
    inputMessage: string;
    setInputMessage: React.Dispatch<React.SetStateAction<string>>;
    isListening: boolean;
    toggleListening: () => void;
}

// Define the ChatInterface component
export default function ChatInterface({
    messages,
    onNewMessage,
    interimTranscript,
    inputMessage,
    setInputMessage,
    isListening,
    toggleListening
}: ChatInterfaceProps) {
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [showPastConversations, setShowPastConversations] = useState(false);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, interimTranscript]);

    // Function to handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (inputMessage.trim()) {
            await onNewMessage(inputMessage);
            setInputMessage('');
        }
    };

    // Function to copy text to clipboard
    const copyToClipboard = (text: string, index: number) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        });
    };

    // Function to handle selecting a past conversation
    const handleSelectConversation = async (conversationId: string) => {
        try {
            const response = await fetch(`${API_URL}/api/conversation/${conversationId}`);
            if (!response.ok) throw new Error('Failed to fetch conversation');
            const data = await response.json();
            
            await onNewMessage(data.messages.join('\n'));
            setShowPastConversations(false);
        } catch (error) {
            console.error('Error fetching conversation:', error);
        }
    };

    return (
        <div className="chat-container">
            <div className="flex flex-row mb-4 justify-between items-center">
                <div className="flex flex-row">
                    <h2 className="text-2xl font-medium text-gray-700 pr-2">Hi, my name is </h2>
                    <h1 className="text-2xl font-semibold">
                        <span className="bg-black text-white px-1 rounded-md">AI</span>
                        <span className="text-gray-900 pl-0.5">ko</span>
                    </h1>
                </div>
                <button
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                    onClick={() => setShowPastConversations(!showPastConversations)}
                >
                    {showPastConversations ? 'Back to Chat' : 'Past Chats '}
                </button>
            </div>
            <div className="chat-box">
                {showPastConversations ? (
                    <PastConversations onSelectConversation={handleSelectConversation} />
                ) : (
                    <>
                        <div className="chat-messages">
                            {messages.map((msg, index) => (
                                <div key={index} className={`message-wrapper ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`message ${msg.isUser ? 'message-user' : 'message-ai'}`}>
                                        {msg.isUser ? (
                                            <p>{msg.text}</p>
                                        ) : msg.isLoading ? (
                                            <div className="flex items-center">
                                                <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                </svg>
                                                Thinking...
                                            </div>
                                        ) : msg.text ? (
                                            <>
                                                <MarkdownWithHTML content={msg.text} />
                                                <button
                                                    onClick={() => copyToClipboard(msg.text, index)}
                                                    className="copy-button"
                                                    aria-label="Copy model response"
                                                >
                                                    <DocumentDuplicateIcon className={`h-5 w-5 ${copiedIndex === index ? 'text-green-500' : 'text-white'}`} />
                                                </button>
                                            </>
                                        ) : null}
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
                                    type="button"
                                    onClick={toggleListening}
                                    className={`voice-button ${isListening ? 'listening' : ''}`}
                                    aria-label={isListening ? 'Stop Listening' : 'Start Listening'}
                                >
                                    <MicrophoneIcon className="h-6 w-6" />
                                </button>
                                <button 
                                    type="submit" 
                                    className="send-button flex flex-row"
                                    disabled={messages.some(msg => msg.isLoading)}
                                >
                                    <PaperAirplaneIcon className="h-6 w-6 pr-2" /> Send
                                </button>
                            </div>
                        </form>
                    </>
                )}
            </div>
        </div>
    );
}