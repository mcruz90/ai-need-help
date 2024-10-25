import React from 'react';
import { PaperAirplaneIcon, MicrophoneIcon, PaperClipIcon } from '@heroicons/react/24/outline';

interface ChatInputProps {
    inputMessage: string;
    setInputMessage: React.Dispatch<React.SetStateAction<string>>;
    onNewMessage: (message: string, files?: File[] | null) => Promise<void>;
    isListening: boolean;
    toggleListening: () => void;
    files: File[];
    setFiles: (files: File[]) => void;
    uploading: boolean;
    uploadMessage?: string | null;
    isProcessing: boolean;
}

export default function ChatInput({
    inputMessage,
    setInputMessage,
    onNewMessage,
    isListening,
    toggleListening,
    files,
    setFiles,
    isProcessing,
    uploadMessage
}: ChatInputProps) {
    const MAX_FILES = 3;
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // ==5MB in bytes
    
    // Validate file size
    const validateFile = (file: File): string | null => {
        if (file.size > MAX_FILE_SIZE) {
            return `File "${file.name}" is too large. Maximum size is 5MB.`;
        }
        return null;
    };

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (inputMessage.trim() || files.length > 0) {
            await onNewMessage(inputMessage, files);
            setInputMessage('');
            setFiles([]);
        }
    };

    // Handle file change
    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            const newFiles = Array.from(event.target.files);
            const totalFiles = files.length + newFiles.length;
            
            if (totalFiles > MAX_FILES) {
                alert(`You can only upload a maximum of ${MAX_FILES} files.`);
                return;
            }
            
            const errors: string[] = [];
            newFiles.forEach(file => {
                const error = validateFile(file);
                if (error) errors.push(error);
            });
            
            if (errors.length > 0) {
                alert(errors.join('\n'));
                return;
            }
            
            setFiles([...files, ...newFiles]);
        }
    };

    // Remove a file from the list
    const removeFile = (indexToRemove: number) => {
        setFiles(files.filter((_, index) => index !== indexToRemove));
    };

    // Helper function to format file size
    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="flex flex-col space-y-2">
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
                    <input
                        type="file"
                        onChange={handleFileChange}
                        className="file-input"
                        aria-label="Upload files"
                        style={{ display: 'none' }}
                        id="file-upload"
                        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                        multiple
                        disabled={files.length >= MAX_FILES}
                    />
                    <label 
                        htmlFor="file-upload" 
                        className={`custom-file-upload ${files.length >= MAX_FILES ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <PaperClipIcon className="h-6 w-6" />
                    </label>
                    <button 
                        type="submit" 
                        className={`send-button flex flex-row items-center justify-center
                            ${isProcessing ? 
                                'bg-gray-500 hover:bg-gray-500 cursor-not-allowed opacity-50' : 
                                'bg-blue-500 hover:bg-blue-600'
                            } 
                            transition-all duration-200 ease-in-out
                            text-white font-semibold py-2 px-4 rounded-lg
                            disabled:opacity-50 disabled:cursor-not-allowed`}
                        disabled={isProcessing}
                    >
                        {isProcessing ? (
                            <span className="flex items-center">
                                <div className="animate-pulse flex space-x-1 mr-2">
                                    <div className="h-1.5 w-1.5 bg-white rounded-full"></div>
                                    <div className="h-1.5 w-1.5 bg-white rounded-full animation-delay-200"></div>
                                    <div className="h-1.5 w-1.5 bg-white rounded-full animation-delay-400"></div>
                                </div>
                                Processing...
                            </span>
                        ) : (
                            <span className="flex items-center">
                                <PaperAirplaneIcon className="h-6 w-6 pr-2" /> 
                                Send
                            </span>
                        )}
                    </button>
                </div>
            </form>
            {/* Uploaded file list display below the input */}
            {files.length > 0 && (
                <div className="space-y-1">
                    {files.map((file, index) => (
                        <div key={index} className="flex items-center space-x-2 px-2 text-sm text-gray-500">
                            <PaperClipIcon className="h-4 w-4" />
                            <span className="truncate">{file.name}</span>
                            <button 
                                onClick={() => removeFile(index)}
                                className="text-red-500 hover:text-red-700"
                                aria-label="Remove file"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
