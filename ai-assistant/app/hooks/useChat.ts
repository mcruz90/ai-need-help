import { useState, useCallback, useRef } from 'react';
import { streamResponse, sendChatMessage, ChatMessage } from '../utils/api';

interface Message {
  text: string;
  isUser: boolean;
  isLoading?: boolean;
  rawText?: string;
  citedText?: string;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const isProcessingRef = useRef(false);

  const handleNewMessage = useCallback(async (message: string) => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    // Add user message to messages and chatHistory
    const userMessage: Message = { text: message, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    setChatHistory(prev => [...prev, { role: 'user', content: message }]);

    // Add loading message
    setMessages(prev => [...prev, { text: '', isUser: false, isLoading: true }]);

    try {
      const response = await sendChatMessage(message, chatHistory);
      let rawResponse = '';
      let citedResponse = '';

      await streamResponse(response, (chunk, isCited) => {
        if (isCited) {
          citedResponse = chunk;
        } else {
          rawResponse += chunk;
          setMessages((prevMessages) => {
            const newMessages = [...prevMessages];
            newMessages[newMessages.length - 1] = { 
              text: rawResponse,
              isUser: false,
              rawText: rawResponse,
              isLoading: false
            };
            return newMessages;
          });
        }
      }).then(() => {
        // Update the message one last time with both responses
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages];
          newMessages[newMessages.length - 1] = { 
            text: citedResponse || rawResponse,
            isUser: false,
            rawText: rawResponse,
            citedText: citedResponse,
            isLoading: false
          };
          return newMessages;
        });
      });

      // Add assistant message to chatHistory
      setChatHistory(prev => [...prev, { role: 'assistant', content: rawResponse }]);
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
