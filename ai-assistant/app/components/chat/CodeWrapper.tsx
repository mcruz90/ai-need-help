// ai-assistant/app/components/chat/CodeWrapper.tsx
import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { DocumentDuplicateIcon } from '@heroicons/react/24/outline';

export type CodeWrapperProps = {
    className?: string;
    children?: React.ReactNode;
    node?: any;
};

const CodeWrapper: React.FC<CodeWrapperProps> = ({ className, children, ...props }) => {
    const [copied, setCopied] = useState(false);
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : '';
    const code = String(children).replace(/\n$/, '');

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(code);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy!', err);
        }
    };

    return (
        <div className="code-block-container">
          <div className="relative">
            <SyntaxHighlighter
                language={language}
                style={oneDark}
                className="prism-code-block"
                customStyle={{
                    padding: '1rem',
                    borderRadius: '0.5rem',
                    maxWidth: '100%',
                }}
            >
                {code}
            </SyntaxHighlighter>
            <button
                onClick={handleCopy}
                className="absolute top-2 right-2 flex justify-center items-center text-white text-sm px-2 py-1 rounded hover:bg-gray-600 transition-colors duration-300 ease-in-out focus:outline-none"
                aria-label="Copy code to clipboard"
            >
                {copied ? 'Copied!' : <DocumentDuplicateIcon className="w-4 h-4" /> }
            </button>
          </div>
            
        </div>
    );
};

export default CodeWrapper;
