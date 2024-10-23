import { useState, useEffect, useCallback, useRef } from 'react';
import { NotionPage, NotionDatabase } from '../components/notion/types';

// Define the useNotion hook to fetch and manage Notion data
export function useNotion() {
  const [pages, setPages] = useState<NotionPage[]>([]);
  const [databases, setDatabases] = useState<NotionDatabase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [expandedPages, setExpandedPages] = useState(new Set<string>());
  const [pageContents, setPageContents] = useState<{ [key: string]: any }>({});
  const [years, setYears] = useState<string[]>([]);
  const [semesters, setSemesters] = useState<string[]>([]);

  // Ref to track if data has been fetched
  const hasFetched = useRef(false);

  useEffect(() => {
    if (!hasFetched.current) {
      fetchNotionData();
      hasFetched.current = true;
    }
  }, []);

  const fetchNotionData = async () => {
    try {
      const response = await fetch('/api/notion');
      const data = await response.json();
      console.log("Data received in useNotion:", data);
      console.log("Pages:", data.pages?.length);
      console.log("Databases:", data.databases?.length);
      console.log("Years:", data.years);
      console.log("Semesters:", data.semesters);

      setPages(data.pages || []);
      setDatabases(data.databases || []);
      
      if (Array.isArray(data.years)) {
        setYears(data.years);
      }
      if (Array.isArray(data.semesters)) {
        setSemesters(data.semesters);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error in useNotion:', err);
      setError(err as Error);
      setLoading(false);
    }
  };

  const togglePageExpansion = useCallback(async (pageId: string) => {
    setExpandedPages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(pageId)) {
        newSet.delete(pageId);
      } else {
        newSet.add(pageId);
        if (!pageContents[pageId]) {
          fetchPageContent(pageId);
        }
      }
      return newSet;
    });
  }, [pageContents]);

  const fetchPageContent = async (pageId: string) => {
    try {
      const response = await fetch(`/api/notion?pageId=${pageId}`);
      const data = await response.json();
      setPageContents(prev => ({ ...prev, [pageId]: data.content }));
    } catch (err) {
      console.error('Error fetching page content:', err);
    }
  };

  return {
    pages,
    databases,
    loading,
    error,
    expandedPages,
    pageContents,
    togglePageExpansion,
    years,
    semesters,
  };
}
