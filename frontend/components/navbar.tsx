'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Brain, CircleUserRound, KeyRound, LogOut, Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
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

  const isActive = (path: string) => pathname === path

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
        <div className="flex h-16 items-center justify-between gap-3">
          <Link href="/" className="flex items-center gap-2 text-xl font-semibold text-primary transition-opacity hover:opacity-80">
            <Brain className="h-6 w-6" />
            <span className="truncate">MemoryVault AI</span>
          </Link>

          {!isLoading && isAuthenticated ? (
            <div className="hidden items-center gap-8 md:flex">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`text-sm font-medium transition-colors ${
                    isActive(item.href)
                      ? 'border-b-2 border-primary text-primary'
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
                  <DropdownMenuItem onClick={() => router.push('/change-password')} variant="purple">
                    <KeyRound className="h-4 w-4" />
                    Change Password
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleLogout} variant="purple">
                    <LogOut className="h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ) : (
            <div className="hidden items-center gap-3 md:flex">
              <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                Login
              </Link>
              <Button size="sm" asChild>
                <Link href="/signup">Sign up</Link>
              </Button>
            </div>
          )}

          <div className="flex items-center md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-10 w-10 rounded-full border border-border"
                  aria-label="Open navigation menu"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-80 px-0 sm:max-w-sm">
                <SheetHeader className="border-b border-border px-6 pb-4 pt-6 text-left">
                  <SheetTitle className="flex items-center gap-2 text-left text-lg text-primary">
                    <Brain className="h-5 w-5" />
                    MemoryVault AI
                  </SheetTitle>
                </SheetHeader>

                <div className="flex flex-1 flex-col gap-6 px-6 py-6">
                  {!isLoading && isAuthenticated ? (
                    <div className="space-y-4">
                      <div className="rounded-lg border border-border bg-muted/40 p-4">
                        <p className="text-sm font-medium text-foreground">{userName || 'User'}</p>
                        <p className="mt-1 break-all text-xs text-muted-foreground">{userEmail || 'No email available'}</p>
                      </div>

                      <div className="flex flex-col gap-2">
                        {navItems.map((item) => (
                          <SheetClose asChild key={item.href}>
                            <Link
                              href={item.href}
                              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                                isActive(item.href)
                                  ? 'bg-primary/10 text-primary'
                                  : 'text-foreground hover:bg-muted'
                              }`}
                            >
                              {item.label}
                            </Link>
                          </SheetClose>
                        ))}

                        <SheetClose asChild>
                          <Button
                            variant="outline"
                            className="mt-2 justify-start"
                            onClick={() => router.push('/change-password')}
                          >
                            <KeyRound className="h-4 w-4" />
                            Change Password
                          </Button>
                        </SheetClose>

                        <SheetClose asChild>
                          <Button
                            variant="ghost"
                            className="justify-start text-destructive hover:bg-destructive/10 hover:text-destructive"
                            onClick={handleLogout}
                          >
                            <LogOut className="h-4 w-4" />
                            Logout
                          </Button>
                        </SheetClose>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3">
                      <SheetClose asChild>
                        <Link
                          href="/login"
                          className="rounded-md border border-border px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                        >
                          Login
                        </Link>
                      </SheetClose>
                      <SheetClose asChild>
                        <Button asChild>
                          <Link href="/signup">Sign up</Link>
                        </Button>
                      </SheetClose>
                    </div>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </nav>
  )
}
