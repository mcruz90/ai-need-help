'use client';

import { useState, useCallback, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import VoiceInterface from './components/VoiceInterface';
import Calendar from './components/calendar/Calendar';
import Sidebar from './components/Sidebar';
import './components/ChatInterface.css';
import './components/CodeBlock.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type ValuePiece = Date | null;
type Value = ValuePiece | [ValuePiece, ValuePiece];

interface ChatMessage {
  role: 'User' | 'Chatbot';
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean }>>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [date, setDate] = useState<Value>(new Date());
  const [interimTranscript, setInterimTranscript] = useState('');
  const [inputMessage, setInputMessage] = useState('');  // Add this new state
  const isProcessingRef = useRef(false);

  const streamResponse = useCallback(async (reader: ReadableStreamDefaultReader<Uint8Array>) => {
    let fullResponse = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = new TextDecoder().decode(value);
      fullResponse += chunk;

      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].text = fullResponse;
        return newMessages;
      });

      // Force immediate update
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    return fullResponse;
  }, []);

  const handleNewMessage = useCallback(async (message: string) => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    setMessages(prev => [...prev, { text: message, isUser: true }, { text: '', isUser: false }]);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...chatHistory, { role: 'User', content: message }]
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      const fullResponse = await streamResponse(reader);

      setChatHistory(prev => [
        ...prev,
        { role: 'User', content: message },
        { role: 'Chatbot', content: fullResponse }
      ]);

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { text: "Sorry, an error occurred.", isUser: false }]);
    } finally {
      isProcessingRef.current = false;
    }
  }, [chatHistory, streamResponse]);

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
              inputMessage={inputMessage}  // Pass the inputMessage state
              setInputMessage={setInputMessage}  // Pass the setInputMessage function
            />
            <VoiceInterface
              onNewMessage={handleNewMessage}
              onInterimTranscript={handleInterimTranscript}
              onFinalTranscript={handleFinalTranscript}  // Add this new prop
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