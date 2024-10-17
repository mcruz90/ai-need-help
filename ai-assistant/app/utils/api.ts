export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export async function sendChatMessage(message: string, chatHistory: ChatMessage[]): Promise<ReadableStreamDefaultReader<Uint8Array>> {
  const messages = [...chatHistory, { role: 'user', content: message }];
  
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ messages }),
  });

  if (!response.body) {
    throw new Error('No response body');
  }

  return response.body.getReader();
}

export async function streamResponse(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onChunk: (text: string, isCited: boolean) => void
): Promise<string> {
  const decoder = new TextDecoder();
  let fullResponse = '';
  let citedResponse = '';
  let isCitedResponse = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    
    if (chunk.includes('__CITATIONS_START__')) {
      isCitedResponse = true;
      citedResponse = '';
      continue;
    }

    if (isCitedResponse) {
      citedResponse += chunk;
      onChunk(citedResponse, true);
    } else {
      fullResponse += chunk;
      onChunk(fullResponse, false);
    }
  }

  return isCitedResponse ? citedResponse : fullResponse;
}
