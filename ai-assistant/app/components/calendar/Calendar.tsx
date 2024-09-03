import React, { useState } from 'react';
import ReactCalendar from 'react-calendar';
import EventForm from './EventForm';
import EventList from './EventList';
import CalendarExport from './CalendarExport';
import 'react-calendar/dist/Calendar.css';
import './calendar.css';

type ValuePiece = Date | null;
type Value = ValuePiece | [ValuePiece, ValuePiece];

interface Event {
  id: string;
  date: Date;
  title: string;
}

const Calendar: React.FC = () => {
  const [date, setDate] = useState<Value>(new Date());
  const [events, setEvents] = useState<Event[]>([]);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);

  const addEvent = (date: Date, title: string) => {
    const newEvent = { id: Date.now().toString(), date, title };
    setEvents([...events, newEvent]);
  };

  const editEvent = (id: string, newTitle: string, newDate: Date) => {
    setEvents(events.map(event => 
      event.id === id ? { ...event, title: newTitle, date: newDate } : event
    ));
    setEditingEvent(null);
  };

  const deleteEvent = (id: string) => {
    setEvents(events.filter(event => event.id !== id));
  };

  return (
    <div className="w-64">
      <ReactCalendar 
        onChange={setDate} 
        value={date}
        tileContent={({ date, view }) => {
          if (view === 'month') {
            const eventForDate = events.find(event => 
              event.date.toDateString() === date.toDateString()
            );
            return eventForDate ? <p className="event-dot">•</p> : null;
          }
        }}
      />
      <EventForm 
        onAddEvent={addEvent} 
        editingEvent={editingEvent}
        onEditEvent={editEvent}
      />
      <EventList 
        events={events} 
        date={date instanceof Date ? date : new Date()} 
        onEditEvent={setEditingEvent}
        onDeleteEvent={deleteEvent}
      />
      <CalendarExport events={events} />
    </div>
  );
};

export default Calendar;
