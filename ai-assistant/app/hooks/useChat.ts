import { useState, useCallback, useRef } from 'react';
import { streamResponse, sendChatMessage, ChatMessage } from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean }>>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const isProcessingRef = useRef(false);

  const handleNewMessage = useCallback(async (message: string) => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    setMessages(prev => [...prev, { text: message, isUser: true }, { text: '', isUser: false }]);

    try {
      const reader = await sendChatMessage(message, chatHistory);
      const fullResponse = await streamResponse(reader, (text) => {
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1].text = text;
          return newMessages;
        });
      });

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

  return { messages, handleNewMessage };
}