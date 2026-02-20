'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Brain, CircleUserRound, KeyRound, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/context/auth-context'

export default function Navbar() {
  const pathname = usePathname()
  const router = useRouter()
  const { isAuthenticated, logout, isLoading, userName, userEmail } = useAuth()

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
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-10 w-10 rounded-full border border-border bg-primary/10 text-primary hover:bg-primary/15"
                      aria-label="Open profile menu"
                    >
                      <CircleUserRound className="h-5 w-5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-64">
                    <DropdownMenuLabel className="space-y-1">
                      <p className="text-sm font-medium text-foreground">{userName || 'User'}</p>
                      <p className="text-xs font-normal text-muted-foreground">{userEmail || 'No email available'}</p>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      onClick={() => router.push('/change-password')}
                      variant="purple"
                    >
                      <KeyRound className="h-4 w-4" />
                      Change Password
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={handleLogout}
                      variant="purple"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
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
