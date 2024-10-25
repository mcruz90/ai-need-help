// cohere-ai.d.ts

import { Stream } from 'stream';

declare module 'cohere-ai' {
  interface StreamedChatResponse {
    
  }

  interface Stream<StreamedChatResponse> extends Stream {
    getReader(): ReadableStreamReader<StreamedChatResponse>;
  }
}
