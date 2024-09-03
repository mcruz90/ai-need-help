import React, { useState, useEffect } from 'react';

interface Event {
  id: string;
  date: Date;
  title: string;
}

interface EventFormProps {
  onAddEvent: (date: Date, title: string) => void;
  onEditEvent: (id: string, newTitle: string, newDate: Date) => void;
  editingEvent: Event | null;
}

const EventForm: React.FC<EventFormProps> = ({ onAddEvent, onEditEvent, editingEvent }) => {
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');

  useEffect(() => {
    if (editingEvent) {
      setTitle(editingEvent.title);
      setDate(editingEvent.date.toISOString().split('T')[0]);
    } else {
      setTitle('');
      setDate('');
    }
  }, [editingEvent]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (title && date) {
      const eventDate = new Date(date);
      eventDate.setMinutes(eventDate.getMinutes() + eventDate.getTimezoneOffset());
      
      if (editingEvent) {
        onEditEvent(editingEvent.id, title, eventDate);
      } else {
        onAddEvent(eventDate, title);
      }
      setTitle('');
      setDate('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mt-4">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Event title"
        className="w-full p-2 mb-2 border rounded"
      />
      <input
        type="date"
        value={date}
        onChange={(e) => setDate(e.target.value)}
        className="w-full p-2 mb-2 border rounded"
      />
      <button type="submit" className="w-full p-2 bg-blue-500 text-white rounded">
        {editingEvent ? 'Update Event' : 'Add Event'}
      </button>
    </form>
  );
};

export default EventForm;
