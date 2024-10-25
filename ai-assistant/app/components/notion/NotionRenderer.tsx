import React, { ReactNode } from 'react';
import { copyToClipboard } from './utils';

function getBlockText(block: any): string {
  switch (block.type) {
    case 'paragraph':
    case 'heading_1':
    case 'heading_2':
    case 'heading_3':
    case 'bulleted_list_item':
    case 'numbered_list_item':
    case 'to_do':
    case 'toggle':
    case 'quote':
    case 'callout':
      return block[block.type].rich_text.map((text: any) => text.plain_text).join('');
    case 'code':
      return block.code.rich_text.map((text: any) => text.plain_text).join('');
    default:
      return '';
  }
}

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

  flushList(); 

  const handleCopy = () => {
    const textContent = blocks.map(block => getBlockText(block)).join('\n');
    copyToClipboard(textContent);
    
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.zIndex = '9999';

    const message = document.createElement('div');
    message.textContent = 'Content Copied!';
    message.style.color = 'white';
    message.style.fontSize = '24px';
    message.style.padding = '20px';
    message.style.backgroundColor = 'green';
    message.style.borderRadius = '10px';

    overlay.appendChild(message);
    document.body.appendChild(overlay);

    setTimeout(() => {
      document.body.removeChild(overlay);
    }, 1500);
  };

  const allContent = (
    <div className="bg-white rounded-lg p-6 mb-4 relative shadow-md">
      {content}
      <button 
        onClick={handleCopy}
        className="absolute top-2 right-2 p-2 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
        title="Copy content"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
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