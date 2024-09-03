import React from 'react';

interface Event {
  id: string;
  date: Date;
  title: string;
}

interface EventListProps {
  events: Event[];
  date: Date;
  onEditEvent: (event: Event) => void;
  onDeleteEvent: (id: string) => void;
}

const EventList: React.FC<EventListProps> = ({ events, date, onEditEvent, onDeleteEvent }) => {
  const eventsForDate = events.filter(
    event => event.date.toDateString() === date.toDateString()
  );

  return (
    <div className="mt-4">
      <h3 className="font-bold">Events for {date.toDateString()}:</h3>
      {eventsForDate.length > 0 ? (
        <ul className="list-none pl-0">
          {eventsForDate.map((event) => (
            <li key={event.id} className="flex justify-between items-center mb-2">
              <span>{event.title}</span>
              <div>
                <button 
                  onClick={() => onEditEvent(event)} 
                  className="mr-2 px-2 py-1 bg-yellow-500 text-white rounded text-sm"
                >
                  Edit
                </button>
                <button 
                  onClick={() => onDeleteEvent(event.id)} 
                  className="px-2 py-1 bg-red-500 text-white rounded text-sm"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>No events for this date.</p>
      )}
    </div>
  );
};

export default EventList;
