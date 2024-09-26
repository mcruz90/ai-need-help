import { useState, useCallback, useRef } from 'react';
import { streamResponse, sendChatMessage, ChatMessage } from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean; isLoading?: boolean }>>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const isProcessingRef = useRef(false);

  const handleNewMessage = useCallback(async (message: string) => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    setMessages(prev => [...prev, { text: message, isUser: true }, { text: '', isUser: false, isLoading: true }]);

    try {
      const response = await sendChatMessage(message, chatHistory);
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      let fullResponse = '';
      await streamResponse(reader, (text) => {
        fullResponse += text;
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = { text: fullResponse, isUser: false, isLoading: false };
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