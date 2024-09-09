'use client';

import { useNotion } from '../../hooks/useNotion';

export function NotionDisplay() {
  const { pages, databases, loading, error } = useNotion();

  if (loading) return <div>Loading Notion data...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Notion Pages</h2>
      {pages.length === 0 ? (
        <p>No pages found.</p>
      ) : (
        <ul className="mb-6">
          {pages.map(page => (
            <li key={page.id} className="mb-2">
              <a 
                href={page.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {(() => {
                  const titleProp = page.properties.title;
                  if (titleProp && 'title' in titleProp) {
                    return titleProp.title[0]?.plain_text;
                  }
                  const nameProp = page.properties as any;
                  if (nameProp.Name && 'title' in nameProp.Name) {
                    return nameProp.Name.title[0]?.plain_text;
                  }
                  return 'Untitled';
                })()}
              </a>
            </li>
          ))}
        </ul>
      )}

      <h2 className="text-xl font-semibold mb-4">Notion Databases</h2>
      {databases.length === 0 ? (
        <p>No databases found.</p>
      ) : (
        <ul>
          {databases.map(db => (
            <li key={db.id} className="mb-2">
              <a 
                href={db.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {db.title?.[0]?.plain_text || 'Untitled'}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}