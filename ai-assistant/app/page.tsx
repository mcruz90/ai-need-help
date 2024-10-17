'use client';

import { useState, useCallback, useEffect } from 'react';
import ChatInterface from './components/chat/ChatInterface';
import { NotionDisplay } from './components/notion/notionDisplay';
import Calendar from './components/calendar/Calendar';
import Sidebar from './components/Sidebar';
import { useChat } from './hooks/useChat';
import { setupVoiceRecognition } from './utils/voiceRecognition';
import './components/chat/ChatInterface.css';
import './components/codeblock/CodeBlock.css';
import TipTapEditor from './components/tiptapeditor/TipTapEditor';
//import NotionTipTapEditor from './components/tiptapeditor/NotionTipTapEditor';

// This is the main page of the app; components are imported from other files and used to build the UI
export default function Home() {
  const { messages, handleNewMessage } = useChat();
  const [interimTranscript, setInterimTranscript] = useState('');
  const [inputMessage, setInputMessage] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isAsideOpen, setIsAsideOpen] = useState(false);
  const [asideContent, setAsideContent] = useState<'notion' | 'calendar' | 'tipTap'>('notion');

  // Interim transcript is the partial transcript as the user is speaking
  const handleInterimTranscript = useCallback((transcript: string) => {
    setInterimTranscript(transcript);
  }, []);

  // Final transcript is the full transcript after the user is done speaking
  const handleFinalTranscript = useCallback((transcript: string) => {
    const finalMessage = transcript.trim();
    setInputMessage(''); 
    setInterimTranscript('');
    if (finalMessage) {
      handleNewMessage(finalMessage); 
    }
  }, [handleNewMessage]);

  const [voiceRecognition, setVoiceRecognition] = useState<any>(null);

  // Setup voice recognition
  useEffect(() => {
    const recognition = setupVoiceRecognition(handleInterimTranscript, handleFinalTranscript);
    setVoiceRecognition(recognition);
    console.log('Voice recognition setup:', recognition);
  }, [handleInterimTranscript, handleFinalTranscript]);

  // Toggle listening to start and stop voice recognition
  const toggleListening = useCallback(() => {
    if (isListening) {
      console.log('Stopping voice recognition');
      voiceRecognition?.stop();
      setIsListening(false);
    } else {
      console.log('Starting voice recognition');
      voiceRecognition?.start();
      setIsListening(true);
    }
  }, [isListening, voiceRecognition]);

  const toggleAside = (content: 'notion' | 'calendar' | 'tipTap') => {
    if (isAsideOpen && asideContent === content) {
      setIsAsideOpen(false);
    } else {
      setIsAsideOpen(true);
      setAsideContent(content);
    }
  };

  // Function to render the active aside component
  const renderAsideContent = () => {
    switch (asideContent) {
      case 'notion':
        return <NotionDisplay />;
      case 'calendar':
        return <Calendar />;
      case 'tipTap':
        return <TipTapEditor />;
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
      <main className={`flex-1 flex flex-col transition-all duration-300 ${isSidebarOpen ? 'ml-64' : 'ml-0'}`}>
        <header className="shadow-sm">
          <div className="w-full px-4 py-3 flex justify-between items-center">
            <h1 className="text-2xl font-semibold">hi</h1>
            <div className="flex flex-row space-x-4">
              <button
                onClick={() => toggleAside('notion')}
                className="menu-button"
              >
                {isAsideOpen && asideContent === 'notion' ? 'Close Notion' : 'Open Notion'}
              </button>
              <button
                onClick={() => toggleAside('calendar')}
                className="menu-button"
              >
                {isAsideOpen && asideContent === 'calendar' ? 'Close Calendar' : 'Open Calendar'}
              </button>
              <button
                onClick={() => toggleAside('tipTap')}
                className="menu-button"
              >
                {isAsideOpen && asideContent === 'tipTap' ? 'Close Editor' : 'Open Editor'}
              </button>
            </div>
          </div>
        </header>
        <div className="flex-1 flex overflow-hidden">
          <section className={`overflow-hidden p-4 transition-all duration-300 ${isAsideOpen ? 'w-[75%]' : 'w-full'}`}>
            <ChatInterface
              messages={messages}
              onNewMessage={handleNewMessage}
              interimTranscript={interimTranscript}
              inputMessage={inputMessage}
              setInputMessage={setInputMessage}
              isListening={isListening}
              toggleListening={toggleListening}
            />
          </section>
          <aside className={` border-l overflow-hidden transition-all duration-300 ${isAsideOpen ? 'w-[25%]' : 'w-0'}`}>
            {isAsideOpen && (
              <div className="h-full flex flex-col">
                <div className="flex-1 overflow-y-auto p-4">
                  {renderAsideContent()}
                </div>
              </div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}