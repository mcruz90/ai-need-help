import React, { useState, useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Client } from '@notionhq/client';

// Initialize Notion client
const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Define types for Notion blocks and Tiptap content
interface RichTextItemRequest {
  type: string;
  text: { content: string; link?: { url: string } | null };
}

interface NotionBlock {
  type: string;
  paragraph?: { rich_text: RichTextItemRequest[] };
  heading_1?: { rich_text: RichTextItemRequest[] };
 
}

interface TiptapNode {
  type: string;
  content?: Array<{ text: string }>;
  attrs?: { level: number };
}

// Notion to Tiptap converter
const notionToTiptap = (notionBlocks: NotionBlock[]): TiptapNode[] => {
  return notionBlocks.map(block => {
    switch (block.type) {
      case 'paragraph':
        return { type: 'paragraph', content: [{ type: 'text', text: block.paragraph?.rich_text[0]?.text.content || '' }] };
      case 'heading_1':
        return { type: 'heading', attrs: { level: 1 }, content: [{ type: 'text', text: block.heading_1?.rich_text[0]?.text.content || '' }] };
      
      default:
        return null;
    }
  }).filter(Boolean) as TiptapNode[];
};

// Tiptap to Notion converter
const tiptapToNotion = (tiptapContent: TiptapNode[]): NotionBlock[] => {
  return tiptapContent.map(node => {
    switch (node.type) {
      case 'paragraph':
        return {
          type: 'paragraph',
          paragraph: { rich_text: [{ type: 'text', text: node.content?.[0]?.text || '' }] }
        };
      case 'heading':
        return {
          type: `heading_${node.attrs?.level}`,
          [`heading_${node.attrs?.level}`]: { rich_text: [{ type: 'text', text: node.content?.[0]?.text || '' }] }
        };
      default:
        return null;
    }
  }).filter(Boolean) as NotionBlock[];
};

const NotionTipTapEditor: React.FC<{ pageId: string }> = ({ pageId }) => {
  const [content, setContent] = useState<TiptapNode[] | null>(null);

  const editor = useEditor({
    extensions: [StarterKit],
    content: content,
    onUpdate: ({ editor }) => {
      setContent(editor.getJSON().content as TiptapNode[]);
    },
  });

  useEffect(() => {
    const fetchNotionContent = async () => {
      const response = await notion.blocks.children.list({ block_id: pageId });
      const tiptapContent = notionToTiptap(response.results as NotionBlock[]);
      setContent(tiptapContent);
    };

    fetchNotionContent();
  }, [pageId]);

  const handleSave = async () => {
    const notionBlocks = tiptapToNotion(content || []);
    
    // Update Notion page
    await notion.blocks.children.append({
      block_id: pageId,
      children: notionBlocks as any,
    });

    console.log('Content saved to Notion');
  };

  if (!editor) {
    return null;
  }

  return (
    <div>
      <EditorContent editor={editor} />
      <button onClick={handleSave}>Save to Notion</button>
    </div>
  );
};

export default NotionTipTapEditor;