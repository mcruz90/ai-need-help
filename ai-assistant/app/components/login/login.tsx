'use client';

import React from 'react';
import { signIn } from 'next-auth/react'
import { useState } from 'react';


export default function LoginPage() {
    const [isLoading, setIsLoading] = useState(false);

    const handleGoogleSignIn = async () => {
      console.log("Sign in button clicked");
      setIsLoading(true);
      try {
        console.log("Attempting to sign in with Google");
        const result = await signIn('google', { 
          callbackUrl: '/dashboard',
          redirect: true
        });
        console.log("Sign in initiated");
      } catch (error) {
        console.error('Error signing in with Google:', error);
      } finally {
        setIsLoading(false);
      }
    };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-background-dark">
      <div className="bg-background-medium p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6 text-center text-button-brand-neutral">Login</h1>
        <form className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-text-light">Email</label>
            <input type="email" id="email" name="email" required className="mt-1 block w-full px-3 py-2 bg-background-dark border border-border-dark rounded-md shadow-sm focus:outline-none focus:ring-button-brand-green focus:border-button-brand-green text-text-dark" />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-text-light">Password</label>
            <input type="password" id="password" name="password" required className="mt-1 block w-full px-3 py-2 bg-background-dark border border-border-dark rounded-md shadow-sm focus:outline-none focus:ring-button-brand-green focus:border-button-brand-green text-text-dark" />
          </div>
          <div className="flex items-center justify-between">
            <a href="#" className="text-sm text-button-brand-green hover:text-button-brand-green-dark">
              Forgot password?
            </a>
          </div>
          <div>
            <button
              type="submit"
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-button-brand-green hover:bg-button-brand-green-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-button-brand-green transition duration-300 ease-in-out"
            >
              Sign in
            </button>
          </div>
        </form>
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border-dark"></div>
            </div>
            <div></div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-background-medium text-text-light">Or continue with</span>
            </div>
          </div>
          <div className="mt-6">
            <button
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full flex items-center justify-center px-4 py-2 border border-border-dark rounded-md shadow-sm text-sm font-medium text-text-light bg-background-dark hover:bg-background-medium"
            >
              <img className="h-5 w-5 mr-2" src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google logo" />
              {isLoading ? 'Signing in...' : 'Sign in with Google'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}