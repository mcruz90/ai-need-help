export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// Define the streamResponse function to handle the streaming of responses from the API
export async function streamResponse(reader: ReadableStreamDefaultReader<Uint8Array>, updateCallback: (text: string) => void) {
  let fullResponse = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = new TextDecoder().decode(value);
    fullResponse += chunk;
    updateCallback(fullResponse);
    await new Promise(resolve => setTimeout(resolve, 0));
  }
  return fullResponse;
}

// Define the sendChatMessage function to send a chat message to the API
export async function sendChatMessage(message: string, chatHistory: ChatMessage[]) {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [...chatHistory, { role: 'user', content: message }]
    }),
  });

  if (!response.ok) throw new Error('Network response was not ok');

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No reader available');

  return reader;
}