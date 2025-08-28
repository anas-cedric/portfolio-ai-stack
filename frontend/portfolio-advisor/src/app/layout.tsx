import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { UserProvider } from "@/contexts/UserContext";
import { Analytics } from "@vercel/analytics/react";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const interDisplay = Inter({
  subsets: ["latin"],
  variable: "--font-inter-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Cedric - AI-powered Wealth Advisor",
  description: "Chat with Cedric to build and refine your investment portfolio",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`min-h-screen ${inter.variable} ${interDisplay.variable} font-sans`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <UserProvider>
            <main className="w-full min-h-screen">
              {children}
            </main>
            <Analytics />
          </UserProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
