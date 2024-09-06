'use client';

import { useState, useCallback } from 'react';
import ChatInterface from './components/ChatInterface';
import VoiceInterface from './components/VoiceInterface';
import Calendar from './components/calendar/Calendar';
import Sidebar from './components/Sidebar';
import { useChat } from './hooks/useChat';
import './components/ChatInterface.css';
import './components/CodeBlock.css';

type ValuePiece = Date | null;
type Value = ValuePiece | [ValuePiece, ValuePiece];

export default function Home() {
  const { messages, handleNewMessage } = useChat();
  const [date, setDate] = useState<Value>(new Date());
  const [interimTranscript, setInterimTranscript] = useState('');
  const [inputMessage, setInputMessage] = useState('');

  const handleInterimTranscript = useCallback((transcript: string) => {
    setInterimTranscript(transcript);
  }, []);

  const handleFinalTranscript = useCallback((transcript: string) => {
    setInputMessage(prev => prev + ' ' + transcript.trim());
    setInterimTranscript('');
  }, []);

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white shadow-sm z-10">
          <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <h1 className="text-2xl font-semibold text-gray-900">Calendar Agent</h1>
          </div>
        </header>
        <div className="flex-1 flex overflow-hidden">
          <section className="w-3/4 overflow-y-auto p-4">
            <ChatInterface
              messages={messages}
              onNewMessage={handleNewMessage}
              interimTranscript={interimTranscript}
              inputMessage={inputMessage}
              setInputMessage={setInputMessage}
            />
            <VoiceInterface
              onNewMessage={handleNewMessage}
              onInterimTranscript={handleInterimTranscript}
              onFinalTranscript={handleFinalTranscript}
            />
          </section>
          <aside className="w-1/4 bg-white p-4 border-l overflow-y-auto">
            <Calendar />
          </aside>
        </div>
      </main>
    </div>
  );
}