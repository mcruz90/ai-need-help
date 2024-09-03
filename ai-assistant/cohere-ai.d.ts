// cohere-ai.d.ts

import { Stream } from 'stream';

declare module 'cohere-ai' {
  interface StreamedChatResponse {
    // Add any properties specific to StreamedChatResponse if needed
  }

  interface Stream<StreamedChatResponse> extends Stream {
    getReader(): ReadableStreamReader<StreamedChatResponse>;
  }
}
