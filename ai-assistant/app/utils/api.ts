export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AgentResponse {
  raw_response: string;
  cited_response: string | null;
  citations: boolean;
}

export async function sendChatMessage(messages: ChatMessage[]): Promise<ReadableStreamDefaultReader<Uint8Array>> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ messages }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`Error processing request: ${JSON.stringify(errorData)}`);
  }

  if (!response.body) {
    throw new Error('No response body');
  }

  return response.body.getReader();
}

export async function sendChatRequestWithFile(
  message: string,
  files: File[] | null,
  chatHistory: ChatMessage[]
): Promise<ReadableStreamDefaultReader<Uint8Array>> {
  const formData = new FormData();
  formData.append('message', message);
  formData.append('chat_history', JSON.stringify(chatHistory));

  if (files && files.length > 0) {
    files.forEach(file => {
      formData.append('files', file); 
    });
  }

  console.log('Sending files:', files?.map(f => f.name));  

  const response = await fetch(`${API_URL}/api/chat/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`Error processing request: ${JSON.stringify(errorData)}`);
  }

  if (!response.body) {
    throw new Error('No response body');
  }

  return response.body.getReader();
}

export async function streamResponse(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onChunk: (data: string, isCited: boolean, isFinal?: boolean) => void
): Promise<void> {
  const decoder = new TextDecoder();
  let buffer = '';
  let isCitedResponse = false;
  let finalResponseReceived = false;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process lines one by one
      let lines = buffer.split('\n');
      buffer = lines.pop() || ''; 

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine === '__CITATIONS_START__') {
          isCitedResponse = true;
          continue;
        }

        if (isCitedResponse) {
          // Cited response chunk
          onChunk(trimmedLine, true);
          isCitedResponse = false; 
          continue;
        }

        // Attempt to parse the line as JSON for the final response
        let parsedJSON: AgentResponse | null = null;
        try {
          parsedJSON = JSON.parse(trimmedLine);
        } catch (jsonError) {
          // Not a JSON chunk; treat as regular content
        }

        if (parsedJSON && typeof parsedJSON === 'object' && 'raw_response' in parsedJSON) {
          // Final JSON response detected
          finalResponseReceived = true;
          onChunk(JSON.stringify(parsedJSON), false, true);
          continue;
        }

        // Regular streamed content
        onChunk(trimmedLine, false);
      }
    }

    // Process any remaining buffer
    if (buffer.trim()) {
      const trimmedBuffer = buffer.trim();

      // Check if the remaining buffer is a JSON object
      let parsedJSON: AgentResponse | null = null;
      try {
        parsedJSON = JSON.parse(trimmedBuffer);
      } catch (jsonError) {
        // Not a JSON chunk; treat as regular content
      }

      if (parsedJSON && typeof parsedJSON === 'object' && 'raw_response' in parsedJSON) {
        onChunk(JSON.stringify(parsedJSON), false, true);
      } else {
        onChunk(trimmedBuffer, false);
      }
    }
  } catch (error) {
    console.error('Error in streamResponse:', error);
    throw error;
  }
}
