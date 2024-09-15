'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { useNotion } from '../../hooks/useNotion';
import { NotionPage, NotionDatabase } from './types';
import { getPageTitle } from './utils';
import { renderNotionContent } from './NotionRenderer';

const ITEMS_PER_PAGE = 10;

export function NotionDisplay() {
  const { 
    pages, 
    databases, 
    loading, 
    error, 
    expandedPages, 
    pageContents, 
    togglePageExpansion, 
    years, 
    semesters 
  } = useNotion();

  console.log("Pages in NotionDisplay:", pages);
  console.log("Years:", years);
  console.log("Semesters:", semesters);

  const [searchTerm, setSearchTerm] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    console.log("Pages updated:", pages.length);
    console.log("Years updated:", years);
    console.log("Semesters updated:", semesters);
  }, [pages, years, semesters]);

  const filteredPages = useMemo(() => {
    return (pages || []).filter((page: NotionPage) => {
      const title = getPageTitle(page);
      const matchesSearch = title.toLowerCase().includes(searchTerm.toLowerCase());
      
      const pageYearSemester = page.properties['Year/Semester'];
      
      if (yearFilter === '' && semesterFilter === '') {
        return matchesSearch;
      }
      
      if (!pageYearSemester || !('multi_select' in pageYearSemester)) {
        return false;
      }

      const pageYears = pageYearSemester.multi_select.filter(item => /^\d{4}$/.test(item.name)).map(item => item.name);
      const pageSemesters = pageYearSemester.multi_select.filter(item => !/^\d{4}$/.test(item.name)).map(item => item.name);

      const matchesYear = yearFilter === '' || pageYears.includes(yearFilter);
      const matchesSemester = semesterFilter === '' || pageSemesters.includes(semesterFilter);

      return matchesSearch && matchesYear && matchesSemester;
    });
  }, [pages, searchTerm, yearFilter, semesterFilter]);

  const paginatedPages = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredPages.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredPages, currentPage]);

  const totalPages = Math.ceil(filteredPages.length / ITEMS_PER_PAGE);

  const filteredDatabases = useMemo(() => {
    return databases.filter((db: NotionDatabase) => 
      (db.title && Array.isArray(db.title) && db.title.length > 0 ? db.title[0]?.plain_text : 'Untitled').toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [databases, searchTerm]);

  const generateExportContent = () => {
    let content = "Notion Pages and Databases\n\n";
    content += "Pages:\n";
    filteredPages.forEach((page: NotionPage) => {
      content += `- ${getPageTitle(page)}\n`;
      content += `  URL: ${page.url}\n`;
      content += "  Properties:\n";
      Object.entries(page.properties).forEach(([key, value]) => {
        content += `    ${key}: `;
        switch (value.type) {
          case 'title':
          case 'rich_text':
            content += value[value.type]?.map((t: any) => t.plain_text).join(', ') || '';
            break;
          case 'multi_select':
            content += value.multi_select?.map((s: any) => s.name).join(', ') || '';
            break;
          case 'select':
            content += value.select?.name || '';
            break;
          case 'date':
            content += `${value.date?.start || ''} - ${value.date?.end || ''}`;
            break;
          case 'checkbox':
            content += value.checkbox ? 'Yes' : 'No';
            break;
          case 'number':
            content += value.number?.toString() || '';
            break;
          case 'url':
            content += value.url || '';
            break;
          case 'email':
            content += value.email || '';
            break;
          case 'phone_number':
            content += value.phone_number || '';
            break;
          case 'formula':
            content += value.formula?.string || value.formula?.number?.toString() || '';
            break;
          case 'relation':
            content += value.relation?.map((r: any) => r.id).join(', ') || '';
            break;
          default:
            content += JSON.stringify(value);
        }
        content += '\n';
      });
      content += '\n';
    });

    content += "\nDatabases:\n";
    filteredDatabases.forEach(db => {
      content += `- ${db.title && Array.isArray(db.title) && db.title.length > 0 ? db.title[0]?.plain_text : 'Untitled'}\n`;
      content += `  URL: ${db.url}\n`;
      content += '\n';
    });
    return content;
  };

  const handleExport = () => {
    const content = generateExportContent();
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'notion_export.txt';
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (loading) return <div className="h-full flex items-center justify-center">Loading Notion data...</div>;
  if (error) return <div className="h-full flex items-center justify-center">Error: {error.message}</div>;

  return (
    <div className="h-full flex flex-col">
      <h2 className="text-xl font-semibold mb-4">Notion Pages and Databases</h2>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search pages and databases..."
          className="w-full p-2 border rounded mb-2"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <div className="flex gap-2">
          <select
            className="w-1/3 p-2 border rounded"
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
          >
            <option value="">All Years</option>
            {years.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          <select
            className="w-1/3 p-2 border rounded"
            value={semesterFilter}
            onChange={(e) => setSemesterFilter(e.target.value)}
          >
            <option value="">All Semesters</option>
            {semesters.map(semester => (
              <option key={semester} value={semester}>{semester}</option>
            ))}
          </select>
          <button
            onClick={handleExport}
            className="w-1/3 p-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Export to Text
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto pr-4">
        <h3 className="text-lg font-semibold mb-2">Pages</h3>
        {paginatedPages.length === 0 ? (
          <p>No pages found.</p>
        ) : (
          <ul className="mb-6">
            {paginatedPages.map(page => (
              <li key={page.id} className="mb-4">
                <div className="flex items-center">
                  <button 
                    onClick={() => togglePageExpansion(page.id)}
                    className="mr-2 p-1 bg-gray-200 rounded"
                  >
                    {expandedPages.has(page.id) ? '▼' : '▶'}
                  </button>
                  <a 
                    href={page.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {getPageTitle(page)}
                  </a>
                </div>
                {expandedPages.has(page.id) && (
                  <div className="mt-2 ml-6 p-2 bg-gray-100 rounded">
                    {pageContents[page.id] ? (
                      <>{renderNotionContent(pageContents[page.id])}</>
                    ) : (
                      <div>Loading...</div>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
        <div className="flex justify-center mt-4">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button
              key={page}
              onClick={() => setCurrentPage(page)}
              className={`mx-1 px-3 py-1 rounded ${
                currentPage === page ? 'bg-blue-500 text-white' : 'bg-gray-200'
              }`}
            >
              {page}
            </button>
          ))}
        </div>

        <h3 className="text-lg font-semibold mb-2 mt-6">Databases</h3>
        {filteredDatabases.length === 0 ? (
          <p>No databases found.</p>
        ) : (
          <ul>
            {filteredDatabases.map(db => (
              <li key={db.id} className="mb-2">
                <a 
                  href={db.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {db.title && Array.isArray(db.title) && db.title.length > 0 ? db.title[0]?.plain_text : 'Untitled'}
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
