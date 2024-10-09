
export function preprocessLatex(content: string): string {
    // Remove \begin{equation} and \end{equation}
    return content.replace(/\\begin\{equation\}/g, '').replace(/\\end\{equation\}/g, '');
}