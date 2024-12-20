import type { Metadata } from "next";
import "./globals.css";
import 'katex/dist/katex.min.css';
import SessionProviderWrapper from '@/app/components/SessionProviderWrapper';

export const metadata: Metadata = {
  title: "AI Need Help",
  description: "Generated by create next app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <SessionProviderWrapper>{children}</SessionProviderWrapper>
      </body>
    </html>
  );
}
