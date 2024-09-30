import { useState, useCallback, useRef } from 'react';
import { streamResponse, sendChatMessage, ChatMessage } from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean; isLoading?: boolean }>>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const isProcessingRef = useRef(false);

  // Define the handleNewMessage function where the chatbot is triggered
  const handleNewMessage = useCallback(async (message: string) => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    setMessages(prev => [...prev, { text: message, isUser: true }, { text: '', isUser: false, isLoading: true }]);

    try {
      const reader = await sendChatMessage(message, chatHistory);
      const fullResponse = await streamResponse(reader, (text) => {
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = { text, isUser: false, isLoading: false };
          return newMessages;
        });
      });

      setChatHistory(prev => [
        ...prev,
        { role: 'user', content: message },
        { role: 'assistant', content: fullResponse }
      ]);

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = { text: "Sorry, an error occurred.", isUser: false, isLoading: false };
        return newMessages;
      });
    } finally {
      isProcessingRef.current = false;
    }
  }, [chatHistory]);

  return { messages, handleNewMessage };
}