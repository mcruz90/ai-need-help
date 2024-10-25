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

// Fetch the content of a single page from Notion
async function handlePageContentRequest(pageId: string) {
  try {
    const blocks = await notion.blocks.children.list({ block_id: pageId });
    return NextResponse.json({ content: blocks.results });
  } catch (error) {
    console.error('Error fetching page content:', error);
    return NextResponse.json({ error: 'Failed to fetch page content' }, { status: 500 });
  }
}

// Fetch all pages from Notion
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

      const pagesWithContent = (searchResponse.results as PageObjectResponse[]).filter(page => {
        
        // Check if the page has properties other than just the title
        return Object.keys(page.properties).length > 1 || 
               (page.properties.title && 'title' in page.properties.title && 
                page.properties.title.title.length > 0 && 
                page.properties.title.title[0].plain_text.trim() !== '');
      });

      allPages = [...allPages, ...pagesWithContent];
      hasMore = searchResponse.has_more;
      startCursor = searchResponse.next_cursor ?? undefined;

      console.log("Fetched pages:", searchResponse.results.length);
      console.log("Pages with content:", pagesWithContent.length);
      console.log("Has more:", hasMore);
      console.log("Next cursor:", startCursor);
    }

    console.log("Total number of pages with content:", allPages.length);

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
