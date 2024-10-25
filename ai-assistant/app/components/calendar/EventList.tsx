import React from 'react';

// Define the Event interface
interface Event {
  id: string;
  date: string;
  time: string;
  description: string;
  location?: string;
  duration: number;
}

// Define the props for the EventList component
interface EventListProps {
  events: Event[];
  date: string;
}

// Define the EventList component 
const EventList: React.FC<EventListProps> = ({ events, date }) => {
  // Filter events for the specified date
  const eventsForDate = events.filter(event => event.date === date);

  return (
    <div className="mt-4">
      {eventsForDate.length === 0 ? (
        <p className="text-gray-500 text-center">No events for this date.</p>
      ) : (
        <ul className="space-y-3">
          {eventsForDate.map(event => (
            <li key={event.id} className="bg-gray-100 rounded-lg p-3 shadow-sm">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-blue-600">{event.time}</span>
                <span className="text-sm text-gray-500">{event.duration} hour{event.duration !== 1 ? 's' : ''}</span>
              </div>
              <p className="text-gray-800 mt-1">{event.description}</p>
              {event.location && (
                <p className="text-sm text-gray-600 mt-1">
                  <span className="fas fa-map-marker-alt mr-1"></span> {event.location}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default EventList;
