import { useState, useEffect, useCallback } from 'react';

interface NotionPage {
  id: string;
  url: string;
  properties: {
    title?: {
      title: Array<{ plain_text: string }>;
    };
  };
}

interface NotionDatabase {
  id: string;
  url: string;
  title: Array<{ plain_text: string }>;
}

// Define the useNotion hook to fetch and manage Notion data
export function useNotion() {
  const [pages, setPages] = useState<NotionPage[]>([]);
  const [databases, setDatabases] = useState<NotionDatabase[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchPages = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/notion?type=pages');
      if (!response.ok) throw new Error('Failed to fetch pages');
      const data = await response.json();
      // console.log('Fetched pages:', data);
      setPages(data);
    } catch (err) {
      console.error('Error fetching pages:', err);
      setError(err instanceof Error ? err : new Error('An error occurred'));
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDatabases = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/notion?type=databases');
      if (!response.ok) throw new Error('Failed to fetch databases');
      const data = await response.json();
      // console.log('Fetched databases:', data);
      setDatabases(data);
    } catch (err) {
      console.error('Error fetching databases:', err);
      setError(err instanceof Error ? err : new Error('An error occurred'));
    } finally {
      setLoading(false);
    }
  }, []);

  const createPage = useCallback(async (databaseId: string, properties: any) => {
    setLoading(true);
    try {
      const response = await fetch('/api/notion/pages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ databaseId, properties }),
      });
      if (!response.ok) throw new Error('Failed to create page');
      const newPage = await response.json();
      setPages(prevPages => [...prevPages, newPage]);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('An error occurred'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPages();
    fetchDatabases();
  }, [fetchPages, fetchDatabases]);

  return {
    pages,
    databases,
    loading,
    error,
    fetchPages,
    fetchDatabases,
    createPage,
  };
}
