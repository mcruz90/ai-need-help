import React from 'react';
import { Squares2X2Icon, UserGroupIcon, BookmarkSquareIcon, Cog6ToothIcon, ChatBubbleOvalLeftEllipsisIcon, Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, setIsOpen }) => {
  const menuItems = [
    { icon: Squares2X2Icon, text: 'Dashboard' },
    { icon: UserGroupIcon, text: 'Agents' },
    { icon: ChatBubbleOvalLeftEllipsisIcon, text: 'Saved Chats' },
    { icon: Cog6ToothIcon, text: 'Settings' },
  ];

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed top-4 left-4 z-20 p-2 rounded-md border border-button-brand-neutral text-button-brand-neutral-dark hover:bg-button-brand-neutral-dark hover:text-gray-900 transition-all duration-300 ${isOpen ? 'ml-60' : 'ml-0'}`}
      >
        {isOpen ? <XMarkIcon className="h-6 w-6" /> : <Bars3Icon className="h-6 w-6" />}
      </button>
      <div className={`fixed top-0 left-0 h-full bg-background shadow-lg transition-all duration-300 ease-in-out z-10 ${isOpen ? 'w-64' : 'w-0'} overflow-hidden`}>
        <div className="p-4">
          <h2 className="text-2xl">Menu</h2>
        </div>
        <nav className="mt-8">
          {menuItems.map(({ icon: Icon, text }) => (
            <a
              key={text}
              href="#"
              className="flex flex-row items-center py-2.5 px-4 rounded transition duration-200 hover:bg-button-brand-yellow hover:text-white"
            >
              <Icon className="h-6 w-6 mr-2" />
              <span>{text}</span>
            </a>
          ))}
        </nav>
      </div>
    </>
  );
};

export default Sidebar;
