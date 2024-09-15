import React, { ReactNode } from 'react';
import { copyToClipboard } from './utils';

export function renderNotionContent(blocks: any[]): ReactNode {
  const content: ReactNode[] = [];
  let currentList: ReactNode[] = [];
  let currentListType: 'bulleted' | 'numbered' | null = null;

  function flushList() {
    if (currentList.length > 0) {
      content.push(
        currentListType === 'bulleted' 
          ? <ul className="list-disc list-inside">{currentList}</ul>
          : <ol className="list-decimal list-inside">{currentList}</ol>
      );
      currentList = [];
      currentListType = null;
    }
  }

  const supportedBlockTypes = new Set([
    'paragraph', 'heading_1', 'heading_2', 'heading_3',
    'bulleted_list_item', 'numbered_list_item', 'to_do',
    'toggle', 'code', 'quote', 'callout'
  ]);

  blocks.forEach((block: { type: string; id: string; [key: string]: any }) => {
    if (!supportedBlockTypes.has(block.type)) {
      console.log(`Unsupported block type: ${block.type}`);
      return;
    }

    let blockContent: ReactNode | null = null;

    switch (block.type) {
      case 'paragraph':
        blockContent = <p>{renderRichText(block.paragraph.rich_text)}</p>;
        break;
      case 'heading_1':
        blockContent = <h1 className="text-2xl font-bold">{renderRichText(block.heading_1.rich_text)}</h1>;
        break;
      case 'heading_2':
        blockContent = <h2 className="text-xl font-semibold">{renderRichText(block.heading_2.rich_text)}</h2>;
        break;
      case 'heading_3':
        blockContent = <h3 className="text-lg font-medium">{renderRichText(block.heading_3.rich_text)}</h3>;
        break;
      case 'bulleted_list_item':
      case 'numbered_list_item':
        const newListType = block.type === 'bulleted_list_item' ? 'bulleted' : 'numbered';
        if (currentListType !== newListType) {
          flushList();
          currentListType = newListType;
        }
        currentList.push(<li key={block.id}>{renderRichText(block[block.type].rich_text)}</li>);
        return;
      case 'to_do':
        blockContent = (
          <div className="flex items-center">
            <input type="checkbox" checked={block.to_do.checked} readOnly className="mr-2" />
            <span>{renderRichText(block.to_do.rich_text)}</span>
          </div>
        );
        break;
      case 'toggle':
        blockContent = (
          <details>
            <summary>{renderRichText(block.toggle.rich_text)}</summary>
            {block.toggle.children && renderNotionContent(block.toggle.children)}
          </details>
        );
        break;
      case 'code':
        blockContent = (
          <pre className="bg-gray-800 text-white p-4 rounded">
            <code>{block.code.rich_text.map((text: any) => text.plain_text).join('')}</code>
          </pre>
        );
        break;
      case 'quote':
        blockContent = (
          <blockquote className="border-l-4 border-gray-300 pl-4 italic">
            {renderRichText(block.quote.rich_text)}
          </blockquote>
        );
        break;
      case 'callout':
        blockContent = (
          <div className="bg-gray-100 p-4 rounded flex items-start">
            {block.callout.icon && <span className="mr-2">{block.callout.icon.emoji}</span>}
            <div>{renderRichText(block.callout.rich_text)}</div>
          </div>
        );
        break;
    }

    if (blockContent) {
      content.push(blockContent);
    }
  });

  flushList(); // Flush any remaining list items

  const allContent = (
    <div className="bg-gray-100 rounded-lg p-4 mb-4 relative">
      {content}
      <button 
        onClick={() => copyToClipboard(blocks.map(block => 
          block[block.type].rich_text.map((text: any) => text.plain_text).join('')
        ).join('\n'))}
        className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
          <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
        </svg>
      </button>
    </div>
  );

  return allContent;
}

export function renderRichText(richText: any[]) {
  return richText.map((text: any, index: number) => {
    let element = text.plain_text;
    if (text.annotations.bold) {
      element = <strong key={index}>{element}</strong>;
    }
    if (text.annotations.italic) {
      element = <em key={index}>{element}</em>;
    }
    if (text.annotations.strikethrough) {
      element = <del key={index}>{element}</del>;
    }
    if (text.annotations.underline) {
      element = <u key={index}>{element}</u>;
    }
    if (text.annotations.code) {
      element = <code key={index}>{element}</code>;
    }
    if (text.href) {
      element = <a key={index} href={text.href} target="_blank" rel="noopener noreferrer">{element}</a>;
    }
    return element;
  });
}