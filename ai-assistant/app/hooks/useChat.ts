import { useState, useCallback, useRef } from 'react';
import { streamResponse, sendChatMessage, sendChatRequestWithFile, ChatMessage, AgentResponse } from '../utils/api';

interface Message {
  text: string;
  isUser: boolean;
  isLoading?: boolean;
  rawText?: string;
  citedText?: string;
  isCited?: boolean;
  showCitations?: boolean;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const isProcessingRef = useRef(false);

  // Handle new messages being sent and received
  const handleNewMessage = useCallback(async (message: string, files?: File[] | null) => {
    if (isProcessingRef.current) {
      console.warn('A message is already being processed.');
      return;
    }

    isProcessingRef.current = true;

    try {
      setMessages(prev => [
        ...prev, 
        { text: message, isUser: true }, 
        { text: '', isUser: false, isLoading: true }
      ]);

      let responseReader;
      if (files && files.length > 0) {
        // Pass the entire files array
        responseReader = await sendChatRequestWithFile(message, files, chatHistory);
      } else {
        responseReader = await sendChatMessage([...chatHistory, { role: 'user', content: message }]);
      }

      let accumulatedResponse = '';

      // Stream the response from the responding backendagent
      await streamResponse(responseReader, (chunk: string, isCited: boolean, isFinal: boolean = false) => {
        try {
          // Check if this is the final JSON response
          if (chunk.includes('"raw_response"')) {
            const parsedResponse = JSON.parse(chunk) as AgentResponse;
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1] = {
                text: parsedResponse.raw_response,
                isUser: false,
                rawText: parsedResponse.raw_response,
                citedText: parsedResponse.cited_response || undefined,
                isCited: parsedResponse.citations,
                showCitations: true,
                isLoading: false
              };
              return newMessages;
            });
            accumulatedResponse = parsedResponse.raw_response;
            return;
          }

          // Handle regular streaming chunks
          try {
            const parsedChunk = JSON.parse(chunk);
            if (parsedChunk.content) {
              
              if (accumulatedResponse && !accumulatedResponse.endsWith(' ') && 
                  !parsedChunk.content.startsWith(' ')) {
                accumulatedResponse += ' ';
              }
              accumulatedResponse += parsedChunk.content;
              
              setMessages(prev => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1] = {
                  text: accumulatedResponse,
                  isUser: false,
                  isLoading: false
                };
                return newMessages;
              });
            }
          } catch (error) {
            
            console.debug('Non-JSON chunk received:', chunk);
          }
        } catch (error) {
          console.error('Error processing chunk:', error);
        }
      });

      // Update chat history
      setChatHistory(prev => [
        ...prev,
        { role: 'user', content: message },
        { role: 'assistant', content: accumulatedResponse }
      ]);

    } catch (error) {
      console.error('Error in handleNewMessage:', error);
      setMessages(prev => {
        const newMessages = [...prev];
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
