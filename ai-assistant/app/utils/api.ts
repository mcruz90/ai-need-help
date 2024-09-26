export const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000/';

export interface ChatMessage {
  role: string;
  content: string;
}

// Define the sendChatMessage function to send a chat message to the API
export async function sendChatMessage(message: string, chatHistory: ChatMessage[]) {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ messages: [...chatHistory, { role: 'User', content: message }] }),
  });

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }

  return response;
}

// Define the streamResponse function to handle the streaming of responses from the API
export async function streamResponse(reader: ReadableStreamDefaultReader<Uint8Array>, onChunk: (text: string) => void) {
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf('\n');
    while (boundary !== -1) {
      const chunk = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 1);

      if (chunk.startsWith('data: ')) {
        const jsonData = chunk.slice(6);
        if (jsonData === '[DONE]') {
          return;
        }
        try {
          const parsedData = JSON.parse(jsonData);
          onChunk(parsedData.message);
        } catch (e) {
          console.error('Error parsing JSON:', e);
        }
      }

      boundary = buffer.indexOf('\n');
    }
  }
}