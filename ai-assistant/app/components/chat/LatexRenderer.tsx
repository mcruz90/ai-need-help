import React from 'react';
import katex from 'katex';

export const LatexRenderer: React.FC<{ latex: string; displayMode: boolean }> = ({ latex, displayMode }) => {
    const containerRef = React.useRef<HTMLSpanElement>(null);

    React.useEffect(() => {
        if (containerRef.current) {
            try {
                katex.render(latex, containerRef.current, {
                    displayMode: displayMode,
                    throwOnError: false,
                    output: 'html',
                    strict: false,
                    trust: true,
                });
            } catch (e) {
                console.error('LaTeX rendering error:', e);
                if (containerRef.current) {
                    containerRef.current.textContent = latex;
                }
            }
        }
    }, [latex, displayMode]);

    return <span ref={containerRef} />;
};

// Function to check if a string contains LaTeX
export const containsLatex = (content: string): boolean => {
    return /\$.*?\$/g.test(content) || /\\begin\{.*?\}/g.test(content) || /\\\[.*?\\\]/g.test(content);
};

// Function to process the content for LaTeX
export const processLatex = (content: string): React.ReactNode => {
    const latexRegex = /(\$.*?\$|\\\[.*?\\\])/g;
    const parts = content.split(latexRegex);
    return parts.map((part, index) => {
        if (part.startsWith('$') && part.endsWith('$')) {
            return (
                <LatexRenderer
                    key={index}
                    latex={part.slice(1, -1)}
                    displayMode={false}
                />
            );
        } else if (part.startsWith('\\[') && part.endsWith('\\]')) {
            return (
                <LatexRenderer
                    key={index}
                    latex={part.slice(2, -2)}
                    displayMode={true}
                />
            );
        }
        return part;
    });
};