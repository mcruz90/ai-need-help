import { useState, useCallback, useRef } from 'react';
import { streamResponse, sendChatMessage, ChatMessage } from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean; isLoading?: boolean; isCited?: boolean }>>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const isProcessingRef = useRef(false);

  const handleNewMessage = useCallback(async (message: string) => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    // Add user message to messages and chatHistory
    const userMessage = { text: message, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    setChatHistory(prev => [...prev, { role: 'user', content: message }]);

    // Add loading message
    setMessages(prev => [...prev, { text: '', isUser: false, isLoading: true }]);

    try {
      const response = await sendChatMessage(message, chatHistory);
      let finalResponse = '';
      await streamResponse(response, (chunk, isCited) => {
        finalResponse = chunk;
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages];
          newMessages[newMessages.length - 1] = { 
            text: finalResponse, 
            isUser: false,
            isCited: isCited
          };
          return newMessages;
        });
      });

      // Add assistant message to chatHistory
      setChatHistory(prev => [...prev, { role: 'assistant', content: finalResponse }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prevMessages) => {
        const newMessages = [...prevMessages];
        newMessages[newMessages.length - 1] = { 
          text: "Sorry, an error occurred.", 
          isUser: false 
        };
        return newMessages;
      });
    } finally {
      isProcessingRef.current = false;
    }
  }, [chatHistory]);

  return { messages, handleNewMessage };
}
