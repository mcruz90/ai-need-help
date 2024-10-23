import React, { useState, useEffect, useRef } from 'react';
import PastConversations from '../pastconversations/PastConversations';
import ChatMessages from './ChatMessages';
import './ChatInterface.css';
import { API_URL } from '../../utils/api';
import ChatInput from './ChatInput'; 
import { useSession } from 'next-auth/react';

// Define the ChatInterfaceProps interface 
interface ChatInterfaceProps {
    messages: Array<{ text: string; isUser: boolean; isLoading?: boolean; isCited?: boolean; rawText?: string; citedText?: string }>;
    onNewMessage: (message: string, files?: File[] | null) => Promise<void>; 
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
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [showPastConversations, setShowPastConversations] = useState(false);
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState(false);
    const [uploadMessage, setUploadMessage] = useState<string | null>(null);
    const { data: session } = useSession();
    const [isProcessing, setIsProcessing] = useState(false);
    
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, interimTranscript]);

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

    const handleSubmit = async (message: string, files: File[] | null = null) => {
        if (!message.trim() && (!files || files.length === 0)) {
            setUploadMessage('Please enter a message or select files to upload.');
            return;
        }

        setIsProcessing(true);
        try {
            await onNewMessage(message, files);
        } catch (error) {
            console.error('Error processing request:', error);
            setUploadMessage('Error processing request. Please try again.');
        } finally {
            setIsProcessing(false);
            setInputMessage('');
            setFiles([]); 
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header section */}
            <div className="flex flex-row mb-4 justify-between items-center p-4">
                <div className="flex flex-row">
                    <h2 className="text-2xl font-medium text-gray-500 pr-2">
                        <span className="bg-black text-white px-1 rounded-md">Hi</span> 
                        {session?.user?.name}, how can I help you today? 
                    </h2>
                </div>
                <button
                    className="action-button-outline"
                    onClick={() => setShowPastConversations(!showPastConversations)}
                >
                    {showPastConversations ? 'Back to Chat' : 'Past Chats '}
                </button>
            </div>

            {/* Main content area */}
            <div className="flex-1 flex flex-col min-h-0 px-4">
                {showPastConversations ? (
                    <PastConversations onSelectConversation={handleSelectConversation} />
                ) : (
                    <>
                        {/* Messages container */}
                        <div className="flex-1 h-0 mb-4 rounded-lg">
                            <ChatMessages messages={messages} interimTranscript={interimTranscript} />
                        </div>

                        {/* ChatInput component */}
                        <div className="flex-shrink-0">
                            <ChatInput
                                inputMessage={inputMessage}
                                setInputMessage={setInputMessage}
                                onNewMessage={handleSubmit}
                                isListening={isListening}
                                toggleListening={toggleListening}
                                files={files} 
                                setFiles={setFiles}
                                isProcessing={isProcessing}
                                uploadMessage={uploadMessage}
                                uploading={uploading}
                            />
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
