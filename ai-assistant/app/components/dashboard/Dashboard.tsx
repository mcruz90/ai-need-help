'use client';

import React from "react";
import { useSession, signOut } from 'next-auth/react';
import { useState, useCallback, useEffect } from 'react';
import ChatInterface from '../chat/ChatInterface';
import { NotionDisplay } from '../notion/notionDisplay';
import Calendar from '../calendar/Calendar';
import Sidebar from '../Sidebar';
import { useChat } from '../../hooks/useChat';
import { setupVoiceRecognition } from '../../utils/voiceRecognition';
import TipTapEditor from '../tiptapeditor/TipTapEditor';

export default function Dashboard() {
  const { data: session, status } = useSession();
    const { messages, handleNewMessage } = useChat();
    const [interimTranscript, setInterimTranscript] = useState('');
    const [inputMessage, setInputMessage] = useState('');
    const [isListening, setIsListening] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isAsideOpen, setIsAsideOpen] = useState(false);
    const [asideContent, setAsideContent] = useState<'notion' | 'calendar' | 'tipTap'>('notion');
  
    // Handle interim transcript (while speaking)
    const handleInterimTranscript = useCallback((transcript: string) => {
      console.log('Interim transcript received:', transcript);
      setInterimTranscript(transcript);
    }, []);
  
    // Handle final transcript (after speaking)
    const handleFinalTranscript = useCallback((transcript: string) => {
      console.log('Final transcript received:', transcript);
      const finalMessage = transcript.trim();
      setInputMessage(finalMessage);
      setInterimTranscript('');
      if (finalMessage) {
        handleNewMessage(finalMessage, null); // Pass null for files when using voice
      }
    }, [handleNewMessage]);
  
    const [voiceRecognition, setVoiceRecognition] = useState<any>(null);
  
    // Setup voice recognition
    useEffect(() => {
      if (typeof window !== 'undefined') {
        const recognition = setupVoiceRecognition(handleInterimTranscript, handleFinalTranscript);
        setVoiceRecognition(recognition);
        console.log('Voice recognition setup complete');
      }
    }, [handleInterimTranscript, handleFinalTranscript]);
  
    // Toggle listening
    const toggleListening = useCallback(() => {
      if (!voiceRecognition) {
        console.warn('Voice recognition not initialized');
        return;
      }

      if (isListening) {
        console.log('Stopping voice recognition');
        voiceRecognition.stop();
        setIsListening(false);
      } else {
        console.log('Starting voice recognition');
        voiceRecognition.start();
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

    if (status === 'loading') {
      return <div>Loading...</div>;
    }
  
    if (!session) {
      return <div>You are not logged in.</div>;
    }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
      <main className={`flex-1 flex flex-col transition-all duration-300 ${isSidebarOpen ? 'ml-64' : 'ml-0'}`}>
        <header className="shadow-sm">
          <div className="w-full px-4 py-3 flex justify-between items-center">
            <div className="flex flex-row space-x-4 justify-end items-end w-full">
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
              <button
                onClick={() => signOut({ callbackUrl: '/' })}
                className="menu-button"
              >
                Sign Out
              </button>
            </div>
          </div>
        </header>
        <div className="flex-1 flex overflow-y-auto">
          <section className={` p-4 transition-all duration-300 ${isAsideOpen ? 'w-[75%]' : 'w-full'}`}>
           
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
