import React from 'react';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import katex from 'katex';
import ReactMarkdown, { Components } from 'react-markdown'; 
import CodeBlock from '../codeblock/CodeBlock';


interface MarkdownBlockProps {
    content: string;
    components?: Components;
}

interface CodeComponentProps {
    node?: any;
    inline?: boolean;
    className?: string;
    children?: React.ReactNode;
    [key: string]: any;
}

const LatexRenderer: React.FC<{ latex: string; displayMode: boolean }> = ({ latex, displayMode }) => {
    const containerRef = React.useRef<HTMLSpanElement>(null);

    React.useEffect(() => {
        if (containerRef.current) {
            katex.render(latex, containerRef.current, {
                displayMode: displayMode,
                throwOnError: false,
                output: 'html',
                strict: false,
                trust: true,
                macros: {
                    "\\eqnarray": "\\begin{align}"
                }
            });
        }
    }, [latex, displayMode]);

    return <span ref={containerRef} className={`katex-container ${displayMode ? 'katex-display' : 'katex-inline'}`} />;
};

const MarkdownBlock: React.FC<MarkdownBlockProps> = ({ content }) => {
    return (
        <ReactMarkdown
            className="markdown-content custom-prose"
            rehypePlugins={[rehypeRaw, rehypeSanitize]}
            components={{
                code({ node, inline, className, children, ...props }: CodeComponentProps) {
                    const match = /language-(\w+)/.exec(className || '');
                    const lang = match && match[1];

                    if (inline) {
                        return <code className={className} {...props}>{children}</code>;
                    }

                    if (lang === 'latex' || lang === 'math') {
                        const latex = String(children).trim();
                        return <LatexRenderer latex={latex} displayMode={true} />;
                    }

                    return (
                        <CodeBlock
                            value={String(children)}
                            language={lang || 'text'}
                        />
                    );
                },
                p({ children }) {
                    if (typeof children === 'string') {
                        const parts = children.split(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g);
                        return (
                            <p>
                                {parts.map((part, index) => {
                                    if (part.startsWith('$$') && part.endsWith('$$')) {
                                        return <LatexRenderer key={index} latex={part.slice(2, -2)} displayMode={true} />;
                                    } else if (part.startsWith('$') && part.endsWith('$')) {
                                        return <LatexRenderer key={index} latex={part.slice(1, -1)} displayMode={false} />;
                                    }
                                    return part;
                                })}
                            </p>
                        );
                    }
                    return <p>{children}</p>;
                },
            }}
        >
            {content}
        </ReactMarkdown>
    );
};

export default MarkdownBlock;