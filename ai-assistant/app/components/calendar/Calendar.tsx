import React, { useState, useEffect, useMemo, useCallback } from 'react';
import EventList from './EventList';
import './calendar.css';
import { API_URL } from '../../utils/api';
import Calendar from 'react-calendar'; 
import 'react-calendar/dist/Calendar.css'; 

// Define types for the calendar
type ValuePiece = Date | null;
type Value = ValuePiece | [ValuePiece, ValuePiece];

// Define types for the events
interface Event {
  id: string;
  date: string;
  time: string;
  description: string;
  location?: string;
  duration: number;
}

// Define the Calendar component
const CalendarComponent: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());

  const formatDate = useCallback((date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }, []);

  // Memoize the current date string
  const currentDateString = useMemo(() => formatDate(currentDate), [currentDate, formatDate]);

  // Function to fetch events from the API
  const fetchEvents = useCallback(async (dateString: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/calendar/events?date=${dateString}`);

      if (!response.ok) throw new Error('Failed to fetch events');
      
      const data = await response.json();
      if (data.events) {
        const formattedEvents: Event[] = data.events.map((event: any) => ({
          ...event,
          date: event.date.split('T')[0],
        }));
        setEvents(formattedEvents);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Effect to fetch events when the current date changes
  useEffect(() => {
    const eventsForCurrentDate = events.some(event => event.date === currentDateString);
    if (!eventsForCurrentDate) {
      fetchEvents(currentDateString);
    }
  }, [currentDateString, events, fetchEvents]);

  // Function to handle date changes
  const handleDateChange = (value: Value) => {
    if (value instanceof Date) {
      setCurrentDate(value);
    }
  };

  // Render the Calendar component
  return (
    <div className="bg-white shadow-lg rounded-lg p-4 w-full">
      <div className="flex flex-col gap-6">
        <div className="w-full">
          <Calendar
            onChange={handleDateChange}
            value={currentDate}
            className="rounded-lg shadow-md mx-auto"
            calendarType="gregory"
          />
        </div>
        <div className="w-full">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            {currentDate.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </h2>
          {isLoading ? (
            <div className="flex justify-center items-center h-32">
              <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
          ) : (
            <EventList 
              events={events} 
              date={formatDate(currentDate)} 
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default CalendarComponent;
