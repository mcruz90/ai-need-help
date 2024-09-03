import { NextResponse } from 'next/server';
import { CohereClient } from 'cohere-ai';

const cohere = new CohereClient({
  token: process.env.COHERE_API_KEY,
});

export async function POST(request: Request) {
  const { message, chatHistory } = await request.json();

  try {
    const stream = await cohere.chatStream({
      chatHistory: chatHistory,
      message: message,
      preamble: "You are a helpful assistant that answers using proper grammar and punctuation.",
      temperature: 0.5,
      maxTokens: 1000,
    });

    const textEncoder = new TextEncoder();
    const readableStream = new ReadableStream({
      async start(controller) {
        for await (const chunk of stream) {
          if (chunk.eventType === 'text-generation') {
            controller.enqueue(textEncoder.encode(chunk.text));
          }
        }
        controller.close();
      },
    });

    return new Response(readableStream, {
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });

  } catch (error) {
    console.error('Error processing request:', error);
    return NextResponse.json({ error: 'An error occurred while processing the request' }, { status: 500 });
  }
}
