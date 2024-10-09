// ai-assistant/app/components/MarkdownRenderer.tsx
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import 'katex/dist/katex.min.css';
import CodeBlock from './CodeBlock';

interface MarkdownRendererProps {
    content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
    return (
        <ReactMarkdown
            children={content}
            className="markdown-content"
            rehypePlugins={[rehypeRaw, rehypeKatex]}
            remarkPlugins={[remarkMath]}
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
        />
    );
};

export default MarkdownRenderer;