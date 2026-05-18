import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { Toaster } from 'sonner'
import { Github } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Navbar from '@/components/navbar'
import { AuthProvider } from '@/context/auth-context'
import './globals.css'

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'MemoryVault AI',
  description: 'Your personal memory assistant powered by AI',
  generator: 'v0.app',
  icons: {
    icon: [
      {
        url: '/icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/apple-icon.png',
  },
}

export const viewport = {
  themeColor: '#6E2594',
  userScalable: false,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased bg-background text-foreground">
        <AuthProvider>
          <Navbar />
          <main className="min-h-screen">
            {children}
          </main>
          <footer className="border-t border-border bg-card/20">
            <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-6 sm:px-6 lg:px-8">
              <div className="text-sm text-muted-foreground">Made by Gourav Kumar Sonu</div>
              <div>
                <Button size="sm" asChild>
                  <a href="https://github.com/gourav05052004/memoryvault-ai" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2">
                      <Github className="h-4 w-4" />
                    <span>GitHub</span>
                  </a>
                </Button>
              </div>
            </div>
          </footer>
          <Toaster position="top-center" richColors />
          <Analytics />
        </AuthProvider>
      </body>
    </html>
  )
}
