'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Brain } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'

export default function Navbar() {
  const pathname = usePathname()
  const router = useRouter()
  const { isAuthenticated, logout, isLoading } = useAuth()

  const isAuthPage = pathname === '/login' || pathname === '/signup'

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const isActive = (path: string) => {
    return pathname === path
  }

  const navItems = [
    { label: 'Upload', href: '/upload' },
    { label: 'Memories', href: '/memories' },
    { label: 'Ask', href: '/ask' },
  ]

  if (isAuthPage) {
    return null
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-card shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/upload" className="flex items-center gap-2 font-semibold text-xl text-primary hover:opacity-80 transition-opacity">
            <Brain className="h-6 w-6" />
            <span>MemoryVault AI</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-8">
            {!isLoading && isAuthenticated ? (
              <>
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`text-sm font-medium transition-colors ${
                      isActive(item.href)
                        ? 'text-primary border-b-2 border-primary'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
                <Button variant="secondary" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                  Login
                </Link>
                <Button size="sm" asChild>
                  <Link href="/signup">Sign up</Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
