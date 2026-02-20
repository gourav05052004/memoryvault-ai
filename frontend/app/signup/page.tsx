'use client'

import { FormEvent, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowRight, Brain, Eye, EyeOff, ShieldCheck, Sparkles } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/context/auth-context'

export default function SignupPage() {
  const router = useRouter()
  const { signup, isAuthenticated, isLoading } = useAuth()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/upload')
    }
  }, [isAuthenticated, isLoading, router])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!name.trim() || !email.trim() || !password.trim()) {
      toast.error('Name, email, and password are required')
      return
    }

    try {
      setSubmitting(true)
      await signup(name, email, password)
      toast.success('Account created successfully')
      router.replace('/upload')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Signup failed'
      toast.error(errorMessage)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-background px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto grid w-full max-w-6xl gap-6 lg:grid-cols-2">
        <Card className="hidden border-border bg-card/50 p-8 lg:flex lg:flex-col lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-xs text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              Create your account
            </div>
            <h1 className="mt-4 text-3xl font-semibold text-foreground">Build your searchable second brain</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Start storing notes, PDFs, and images in one place with smart retrieval built in.
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-start gap-3 rounded-lg border border-border bg-background p-3">
              <ShieldCheck className="mt-0.5 h-4 w-4 text-primary" />
              <p className="text-sm text-muted-foreground">Private-by-default memories with secure JWT authentication.</p>
            </div>
            <div className="flex items-start gap-3 rounded-lg border border-border bg-background p-3">
              <Brain className="mt-0.5 h-4 w-4 text-primary" />
              <p className="text-sm text-muted-foreground">AI-powered summaries, tags, and semantic memory recall.</p>
            </div>
          </div>
        </Card>

        <Card className="w-full border-border bg-card p-6 shadow-md sm:p-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-foreground">Create account</h2>
              <p className="mt-1 text-sm text-muted-foreground">Sign up to start using MemoryVault AI</p>
            </div>
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <Brain className="h-5 w-5 text-primary" />
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="signup-name">Name</Label>
              <Input
                id="signup-name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Your name"
                disabled={submitting}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-email">Email</Label>
              <Input
                id="signup-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                disabled={submitting}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-password">Password</Label>
              <div className="relative">
                <Input
                  id="signup-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="At least 8 characters"
                  disabled={submitting}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((previous) => !previous)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  disabled={submitting}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full gap-2" disabled={submitting}>
              {submitting ? 'Creating account...' : 'Sign up'}
              {!submitting && <ArrowRight className="h-4 w-4" />}
            </Button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Login
            </Link>
          </p>
        </Card>
      </div>
    </div>
  )
}
