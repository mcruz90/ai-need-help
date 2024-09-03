import React from 'react';
import { createEvents } from 'ics';

interface Event {
  date: Date;
  title: string;
}

interface CalendarExportProps {
  events: Event[];
}

const CalendarExport: React.FC<CalendarExportProps> = ({ events }) => {
  const exportEvents = () => {
    const icsEvents = events.map(event => ({
      start: [
        event.date.getFullYear(),
        event.date.getMonth() + 1,
        event.date.getDate(),
        event.date.getHours(),
        event.date.getMinutes()
      ] as [number, number, number, number, number],
      title: event.title,
      duration: { hours: 1 } // Assuming 1-hour duration for each event
    }));

    createEvents(icsEvents, (error, value) => {
      if (error) {
        console.log(error);
        return;
      }

      const blob = new Blob([value as string], { type: 'text/calendar;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'calendar.ics');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  };

  return (
    <button 
      onClick={exportEvents}
      className="mt-4 w-full p-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
    >
      Export to Google Calendar
    </button>
  );
};

export default CalendarExport;
