export interface YearSemester {
  year: string;
  semester: string;
}

export interface NotionPage {
  id: string;
  url: string;
  properties: {
    title?: {
      title: Array<{ plain_text: string }>;
    };
    'Year/Semester'?: {
      multi_select: Array<{ name: string }>;
    };
    [key: string]: any;
  };
}

export interface NotionDatabase {
  id: string;
  url: string;
  title: Array<{ plain_text: string }>;
}

export interface NotionPropertyValue {
  type: string;
  title?: Array<{ plain_text: string }>;
  rich_text?: Array<{ plain_text: string }>;
  multi_select?: Array<{ name: string }>;
  select?: { name: string };
  date?: { start: string; end: string | null };
  checkbox?: boolean;
  number?: number;
  url?: string;
  email?: string;
  phone_number?: string;
  formula?: { type: string; string?: string; number?: number };
  relation?: Array<{ id: string }>;
  [key: string]: any;
}