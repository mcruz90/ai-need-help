import { NextResponse } from 'next/server';
import { Client, LogLevel } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN, logLevel: LogLevel.DEBUG });

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type');

  try {
    let response;
    switch (type) {
      case 'pages':
      case 'databases':
        response = await notion.search({});
        break;
      default:
        return NextResponse.json({ error: 'Invalid type parameter' }, { status: 400 });
    }
    
    // console.log(`Notion API response for ${type}:`, response);
    const filteredResults = response.results.filter(item => {
      if (type === 'pages') return item.object === 'page';
      if (type === 'databases') return item.object === 'database';
      return false;
    });
    return NextResponse.json(filteredResults);
  } catch (error) {
    console.error('Error fetching data from Notion:', error);
    return NextResponse.json({ error: 'Error fetching data from Notion' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const { databaseId, properties } = await request.json();
    const response = await notion.pages.create({
      parent: { database_id: databaseId },
      properties: properties,
    });
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({ error: 'Error creating page in Notion' }, { status: 500 });
  }
}
