import React, { useMemo, memo } from 'react';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import ReactMarkdown from 'react-markdown';
import CodeWrapper from './CodeWrapper';
import remarkGfm from 'remark-gfm';
import 'katex/dist/katex.min.css';
import './markdown-styles.css';
import { containsLatex, processLatex } from './LatexRenderer';

interface MarkdownBlockProps {
    content: string;
}

const MarkdownBlock: React.FC<MarkdownBlockProps> = ({ content }) => {
    const safeContent = useMemo(() => {
        if (!content) return '';

        // Clean up the content
        return content
            .replace(/\\"/g, '"')
            .replace(/\\n/g, '\n')
            .replace(/\\t/g, '\t')
            .replace(/\\/g, '')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
    }, [content]);

    return (
        <ReactMarkdown
            className="markdown-content custom-prose"
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[
                rehypeRaw,
                [rehypeSanitize, {
                    attributes: {
                        a: ['href', 'target', 'rel', 'className'],
                        span: ['className', 'ref'],
                        div: ['className'],
                        p: ['className'],
                        code: ['className', 'inline'],
                        pre: ['className']
                    }
                }]
            ]}
            components={{
                code: ({ node, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');

                    if (match == null) {
                        return (
                            <code className="inline-code" {...props}>
                                {children}
                            </code>
                        );
                    }

                    return (
                        <CodeWrapper
                            node={node}
                            className={className}
                            {...props}
                        >
                            {children}
                        </CodeWrapper>
                    );
                },
                p: ({ node, children }) => {
                    const hasBlockElements = React.Children.toArray(children).some(
                        child => React.isValidElement(child) &&
                            child.props?.node?.type === 'element' &&
                            ['pre', 'div', 'code'].includes(child.props.node.tagName)
                    );

                    if (hasBlockElements) {
                        return <>{children}</>;
                    }

                    if (typeof children === 'string') {
                        if (containsLatex(children)) {
                            return <p className="mb-4">{processLatex(children as string)}</p>;
                        }

                        const paragraphs = children.split(/\n\n+/).map((text, i) => (
                            <p key={i} className="mb-4">
                                {text.split('\n').map((line, j) => (
                                    <React.Fragment key={j}>
                                        {line}
                                        {j !== text.split('\n').length - 1 && <br />}
                                    </React.Fragment>
                                ))}
                            </p>
                        ));
                        return <>{paragraphs}</>;
                    }
                    return <p className="mb-4">{children}</p>;
                },
                a: ({ href, children, ...props }) => {
                    const citationMatch = href?.match(/\[(\d+)\]$/);
                    const citation = citationMatch ? `[${citationMatch[1]}]` : '';

                    return (
                        <a
                            href={href}
                            className="inline-flex items-center text-blue-600 hover:text-blue-800 visited:text-purple-600"
                            target="_blank"
                            rel="noopener noreferrer"
                            {...props}
                        >
                            {children}
                            {citation && <sup className="ml-0.5 text-xs">{citation}</sup>}
                        </a>
                    );
                }
            }}
        >
            {safeContent}
        </ReactMarkdown>
    );
};

export default memo(MarkdownBlock);
