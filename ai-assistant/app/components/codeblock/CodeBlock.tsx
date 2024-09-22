import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './CodeBlock.css';

interface CodeBlockProps {
  value: string;
  language: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ value, language }) => {
  const [copied, setCopied] = useState(false);

  // Remove backticks and extract language if present
  const processedValue = value.replace(/^```(\w+)?\n/, '').replace(/```$/, '');
  const processedLanguage = language || value.match(/^```(\w+)/)?.[1] || 'text';

  const copyToClipboard = () => {
    navigator.clipboard.writeText(processedValue).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="relative my-4">
      <button
        onClick={copyToClipboard}
        className="absolute top-2 right-2 bg-gray-700 text-white text-sm px-2 py-1 rounded hover:bg-gray-600 focus:outline-none"
        aria-label="Copy code to clipboard"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>
      <SyntaxHighlighter
        language={processedLanguage}
        style={tomorrow}
        customStyle={{
          margin: 0,
          padding: '1rem',
          borderRadius: '0.5rem',
          background: '#1e293b', // Tailwind's gray-800
          fontSize: '0.875rem', // text-sm
          lineHeight: '1.25rem', // leading-5
          overflowX: 'auto',
        }}
        showLineNumbers
        wrapLines
        className="prism-code-block"
      >
        {processedValue}
      </SyntaxHighlighter>
    </div>
  );
};

export default CodeBlock;