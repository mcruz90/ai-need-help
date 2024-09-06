import React from 'react';
import { Squares2X2Icon, UserGroupIcon, BookmarkSquareIcon, Cog6ToothIcon, ChatBubbleOvalLeftEllipsisIcon } from '@heroicons/react/24/outline';

const Sidebar = () => {
  return (
    <div className="w-64 bg-white h-full">
      <div className="p-4">
        <h2 className="text-2xl">Menu</h2>
      </div>
      <nav className="mt-8 ">
        <a href="#" className="flex flex-row py-2.5 px-4 rounded transition duration-200 hover:bg-brand-orange hover:text-white">
          <Squares2X2Icon className ="h-6 w-6 pr-2" /> Dashboard
        </a>
        <a href="#" className="flex flex-row py-2.5 px-4 rounded transition duration-200 hover:bg-brand-orange hover:text-white">
          <UserGroupIcon className ="h-6 w-6 pr-2" /> Agents
        </a>
        <a href="#" className="flex flex-row py-2.5 px-4 rounded transition duration-200 hover:bg-brand-orange hover:text-white">
          <ChatBubbleOvalLeftEllipsisIcon className ="h-6 w-6 pr-2" /> Saved Chats
        </a>
        <a href="#" className="flex flex-row py-2.5 px-4 rounded transition duration-200 hover:bg-brand-orange hover:text-white">
          <Cog6ToothIcon className ="h-6 w-6 pr-2" />Settings
        </a>
      </nav>
    </div>
  );
};

export default Sidebar;