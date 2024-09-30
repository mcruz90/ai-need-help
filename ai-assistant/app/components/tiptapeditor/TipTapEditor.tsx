
import { Color } from '@tiptap/extension-color';
import ListItem from '@tiptap/extension-list-item';
import TextStyle from '@tiptap/extension-text-style';
import { EditorProvider, useCurrentEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import React from 'react';
import { BoldIcon, 
    ItalicIcon,
    StrikethroughIcon,
    CodeBracketIcon,
    ArrowTurnDownLeftIcon,
    ArrowTurnDownRightIcon,
    H1Icon,
    H2Icon,
    H3Icon, 
    ListBulletIcon,
    NumberedListIcon,
    MinusCircleIcon, 
    ArrowRightIcon,
    XMarkIcon, 
    ArrowUturnLeftIcon,
    ArrowUturnRightIcon} from '@heroicons/react/24/outline';
import { MinusIcon } from '@heroicons/react/24/outline';

const MenuBar = () => {
  const { editor } = useCurrentEditor();

  if (!editor) {
    return null;
  }

  return (
    <div className="control-group border-b border-b-gray-300">
      <div className="button-group">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          disabled={!editor.can().chain().focus().toggleBold().run()}
          className={editor.isActive('bold') ? 'is-active' : ''}
        >
          <BoldIcon className="h-6 w-6"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          disabled={!editor.can().chain().focus().toggleItalic().run()}
          className={editor.isActive('italic') ? 'is-active' : ''}
        >
          <ItalicIcon className="h-6 w-6"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleStrike().run()}
          disabled={!editor.can().chain().focus().toggleStrike().run()}
          className={editor.isActive('strike') ? 'is-active' : ''}
        >
          <StrikethroughIcon className="h-5 w-5"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleCode().run()}
          disabled={!editor.can().chain().focus().toggleCode().run()}
          className={editor.isActive('code') ? 'is-active' : ''}
        >
          <CodeBracketIcon className="h-5 w-5"/>
        </button>
        <button onClick={() => editor.chain().focus().unsetAllMarks().run()}>
          <MinusCircleIcon className="h-5 w-5" aria-label="Undo All Styles"/>
        </button>
        <button onClick={() => editor.chain().focus().clearNodes().run()}>
          <XMarkIcon className="h-5 w-5" aria-label="Clear Formatting"/>
        </button>
        <button
          onClick={() => editor.chain().focus().setParagraph().run()}
          className={editor.isActive('paragraph') ? 'is-active' : ''}
        >
          <ArrowTurnDownLeftIcon className="h-5 w-5 mx-1" aria-label="New Paragraph"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={editor.isActive('heading', { level: 1 }) ? 'is-active' : ''}
        >
          <H1Icon className="h-5 w-5 mx-1" aria-label="Heading 1"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={editor.isActive('heading', { level: 2 }) ? 'is-active' : ''}
        >
          <H2Icon className="h-5 w-5 mx-1" aria-label="Heading 2"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={editor.isActive('heading', { level: 3 }) ? 'is-active' : ''}
        >
          <H3Icon className="h-5 w-5 mx-1" aria-label="Heading 3"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={editor.isActive('bulletList') ? 'is-active' : ''}
        >
          <ListBulletIcon className="h-5 w-5 mx-1" aria-label="Bullet List"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={editor.isActive('orderedList') ? 'is-active' : ''}
        >
          <NumberedListIcon className="h-5 w-5" aria-label="Numbered List"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={editor.isActive('codeBlock') ? 'is-active' : ''}
        >
          <CodeBracketIcon className="h-5 w-5" aria-label="Code Block"/>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          className={editor.isActive('blockquote') ? 'is-active' : ''}
        >
          <ArrowTurnDownRightIcon className="h-5 w-5" aria-label="Blockquote"/>
        </button>
        <button onClick={() => editor.chain().focus().setHorizontalRule().run()}>
          <MinusIcon className="h-5 w-5" aria-label="Horizontal Rule"/>
        </button>
        <button onClick={() => editor.chain().focus().setHardBreak().run()}>
          <ArrowRightIcon className="h-5 w-5" aria-label="Hard Break"/>
        </button>
        <button
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().chain().focus().undo().run()}
        >
          <ArrowUturnLeftIcon className="h-5 w-5" aria-label="Undo"/>
        </button>
        <button
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().chain().focus().redo().run()}
        >
          <ArrowUturnRightIcon className="h-5 w-5" aria-label="Redo"/>
        </button>
        <button
          onClick={() => editor.chain().focus().setColor('#958DF1').run()}
          className={editor.isActive('textStyle', { color: '#958DF1' }) ? 'is-active' : ''}
        >
          Purple
        </button>
      </div>
    </div>
  );
};

const extensions = [
  Color.configure({ types: [TextStyle.name, ListItem.name] }),
  TextStyle.configure(),
  StarterKit.configure({
    bulletList: {
      keepMarks: true,
      keepAttributes: false,
    },
    orderedList: {
      keepMarks: true,
      keepAttributes: false,
    },
  }),
];

const TipTapEditor: React.FC = () => {
  const content = `
    <h2>Hi there,</h2>
    <p>This is a <em>basic</em> example of <strong>Tiptap</strong>.</p>
    <p>Feel free to edit this content!</p>
  `;

  return (
    <div className="border border-gray-300">
    <EditorProvider slotBefore={<MenuBar />} extensions={extensions} content={content} />
    </div>
  );
};

export default TipTapEditor;