import { NotionPage, NotionPropertyValue } from './types';

export function getPageTitle(page: NotionPage): string {
  if (page.properties) {
    const titleProp = page.properties.title as NotionPropertyValue | undefined;
    if (titleProp && 'title' in titleProp && titleProp.title && titleProp.title.length > 0) {
      return titleProp.title[0].plain_text;
    }

    const nameProp = page.properties.Name as NotionPropertyValue | undefined;
    if (nameProp && 'title' in nameProp && nameProp.title && nameProp.title.length > 0) {
      return nameProp.title[0].plain_text;
    }

    for (const [, value] of Object.entries(page.properties)) {
      const prop = value as NotionPropertyValue;
      if (typeof prop === 'object' && prop !== null && 'title' in prop) {
        const titleArray = prop.title;
        if (Array.isArray(titleArray) && titleArray.length > 0) {
          return titleArray[0].plain_text;
        }
      }
    }
  }

  return 'Untitled';
}

export function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).then(() => {
    console.log('Content copied to clipboard');
  }).catch(err => {
    console.error('Failed to copy: ', err);
  });
}
