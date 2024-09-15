import { NextRequest, NextResponse } from 'next/server';
import { Client } from '@notionhq/client';
import { PageObjectResponse } from '@notionhq/client/build/src/api-endpoints';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const pageId = url.searchParams.get('pageId');

  if (pageId) {
    return handlePageContentRequest(pageId);
  } else {
    return handleMainNotionDataRequest();
  }
}

async function handlePageContentRequest(pageId: string) {
  try {
    const blocks = await notion.blocks.children.list({ block_id: pageId });
    return NextResponse.json({ content: blocks.results });
  } catch (error) {
    console.error('Error fetching page content:', error);
    return NextResponse.json({ error: 'Failed to fetch page content' }, { status: 500 });
  }
}

async function handleMainNotionDataRequest() {
  try {
    let allPages: PageObjectResponse[] = [];
    let hasMore = true;
    let startCursor: string | undefined = undefined;

    while (hasMore) {
      const searchResponse = await notion.search({
        filter: {
          property: 'object',
          value: 'page'
        },
        start_cursor: startCursor,
        page_size: 100,
      });

      allPages = [...allPages, ...searchResponse.results as PageObjectResponse[]];
      hasMore = searchResponse.has_more;
      startCursor = searchResponse.next_cursor ?? undefined;

      console.log("Fetched pages:", searchResponse.results.length);
      console.log("Has more:", hasMore);
      console.log("Next cursor:", startCursor);
    }

    console.log("Total number of pages fetched:", allPages.length);

    const databasesResponse = await notion.search({
      filter: {
        property: 'object',
        value: 'database',
      },
    });

    const years = new Set<string>();
    const semesters = new Set<string>();
    allPages.forEach((page: PageObjectResponse) => {
      const yearSemester = (page.properties['Year/Semester'] as any)?.multi_select || [];
      yearSemester.forEach((item: { name: string }) => {
        if (/^\d{4}$/.test(item.name)) {
          years.add(item.name);
        } else {
          semesters.add(item.name);
        }
      });
    });

    console.log("Extracted years:", Array.from(years));
    console.log("Extracted semesters:", Array.from(semesters));

    return NextResponse.json({
      pages: allPages,
      databases: databasesResponse.results,
      years: Array.from(years),
      semesters: Array.from(semesters),
    });
  } catch (error) {
    console.error('Error fetching Notion data:', error);
    return NextResponse.json({ error: 'Failed to fetch Notion data' }, { status: 500 });
  }
}
