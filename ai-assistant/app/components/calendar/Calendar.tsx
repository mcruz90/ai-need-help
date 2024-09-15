import React, { useState, useEffect, useCallback, useMemo } from 'react';
import EventList from './EventList';
import './calendar.css';
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

  const formatDate = useMemo(() => (date: Date): string => {
    return date.toISOString().split('T')[0];
  }, []);

  const fetchEvents = useCallback(async (date: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/calendar/events?date=${date}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setEvents(data.events);
    } catch (error) {
      console.error("Error fetching events:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const formattedDate = formatDate(currentDate);
    fetchEvents(formattedDate);
  }, [currentDate, fetchEvents, formatDate]);

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
