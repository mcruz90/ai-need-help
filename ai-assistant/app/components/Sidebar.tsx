import React from 'react';
import { Squares2X2Icon, UserGroupIcon, BookmarkSquareIcon, Cog6ToothIcon, ChatBubbleOvalLeftEllipsisIcon } from '@heroicons/react/24/outline';

// Define the Sidebar component
const Sidebar = () => {
  // Define the menu items
  const menuItems = [
    { icon: Squares2X2Icon, text: 'Dashboard' },
    { icon: UserGroupIcon, text: 'Agents' },
    { icon: ChatBubbleOvalLeftEllipsisIcon, text: 'Saved Chats' },
    { icon: Cog6ToothIcon, text: 'Settings' },
  ];

  return (
    <div className="w-64 bg-white h-full">
      <div className="p-4">
        <h2 className="text-2xl">Menu</h2>
      </div>
      <nav className="mt-8">
        {menuItems.map(({ icon: Icon, text }) => (
          <a
            key={text}
            href="#"
            className="flex flex-row py-2.5 px-4 rounded transition duration-200 hover:bg-brand-orange hover:text-white"
          >
            <Icon className="h-6 w-6 pr-2" />
            {text}
          </a>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;