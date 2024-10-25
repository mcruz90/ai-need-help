'use client';

import React from "react";
import { useSession } from "next-auth/react";
import Dashboard from './dashboard/Dashboard';
import LoginPage from './login/login';

export default function ClientWrapper() {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  return session ? <Dashboard /> : <LoginPage />;
}