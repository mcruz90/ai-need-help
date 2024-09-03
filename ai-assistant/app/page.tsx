'use client';

import { useState, useCallback, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import VoiceInterface from './components/VoiceInterface';
import Calendar from './components/calendar/Calendar';
import './components/ChatInterface.css';
import './components/CodeBlock.css';

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

  const handleNewMessage = useCallback(async (message: string) => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    // Add user message to messages state
    setMessages(prev => [...prev, { text: message, isUser: true }]);
    
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          messages: [
            ...chatHistory,
            { role: 'User', content: message }
          ]
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      // Add an empty AI message that we'll update as we receive the response
      setMessages(prev => [...prev, { text: '', isUser: false }]);

      let fullResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = new TextDecoder().decode(value);
        fullResponse += chunk;
        
        // Update the AI message as we receive more of the response
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].text = fullResponse;
          return newMessages;
        });
      }

      // Update chat history
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
  }, [chatHistory]);

  const handleInterimTranscript = useCallback((transcript: string) => {
    setInterimTranscript(transcript);
  }, []);

  const handleFinalTranscript = useCallback((transcript: string) => {
    setInputMessage(prev => prev + ' ' + transcript.trim());
    setInterimTranscript('');
  }, []);

  return (
    <main className="flex min-h-screen p-4">
      <div className="flex-grow mr-4">
        <h1 className="text-4xl font-bold mb-8">Personal AI Assistant</h1>
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
      </div>
      <Calendar />
    </main>
  );
}
