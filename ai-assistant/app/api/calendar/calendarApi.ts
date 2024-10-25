import { API_URL } from '../../utils/api'

export interface Event {
  id: string;
  date: string;
  time: string;
  description: string;
  location?: string;
  duration: number;
}

export interface EventsResponse {
  events: Event[];
}

export async function fetchCalendarEvents(date: string): Promise<Event[]> {
  try {
    const response = await fetch(`${API_URL}/api/calendar/events?date=${date}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data: EventsResponse = await response.json();
    return data.events;
  } catch (error) {
    console.error("Error fetching events:", error);
    return [];
  }
}