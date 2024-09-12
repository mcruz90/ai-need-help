import React, { useState, useEffect } from 'react';
import { API_URL } from '../utils/api';

interface Conversation {
  id: string;
  title: string;
  timestamp: string;
}

// Define the PastConversations component
const PastConversations: React.FC<{ onSelectConversation: (id: string) => void }> = ({ onSelectConversation }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Use effect to fetch conversations from the API
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const response = await fetch(`${API_URL}/api/chat/past-conversations`);
        if (!response.ok) throw new Error('Failed to fetch conversations');
        const data = await response.json();
        setConversations(data.conversations);
      } catch (error) {
        console.error('Error fetching conversations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, []);

  if (isLoading) {
    return <div>Loading past conversations...</div>;
  }

  return (
    <div className="bg-white shadow-lg rounded-lg p-4 w-full">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">Past Conversations</h2>
      {conversations.length === 0 ? (
        <p className="text-gray-500">No past conversations found.</p>
      ) : (
        <ul className="space-y-2">
          {conversations.map((conversation) => (
            <li 
              key={conversation.id}
              className="bg-gray-100 rounded-lg p-3 cursor-pointer hover:bg-gray-200 transition-colors"
              onClick={() => onSelectConversation(conversation.id)}
            >
              <h3 className="font-semibold text-blue-600">{conversation.title}</h3>
              <p className="text-sm text-gray-600">{conversation.timestamp}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PastConversations;