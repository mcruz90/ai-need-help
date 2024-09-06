import type { Metadata } from "next";
import "./globals.css";
import './markdown-styles.css';

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
      <body>{children}</body>
    </html>
  );
}
