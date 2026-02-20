'use client'

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { getCurrentUserProfile, loginUser, signupUser } from '@/lib/api'

const TOKEN_STORAGE_KEY = 'memoryvault_token'
const NAME_STORAGE_KEY = 'memoryvault_user_name'
const EMAIL_STORAGE_KEY = 'memoryvault_user_email'

function toTitleCase(value: string): string {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
}

function deriveNameFromEmail(email: string): string {
  const localPart = email.split('@')[0] || ''
  const cleaned = localPart.replace(/[._-]+/g, ' ').trim()
  return toTitleCase(cleaned || 'User')
}

function decodeTokenEmail(token: string): string | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const normalizedPayload = payload.replace(/-/g, '+').replace(/_/g, '/')
    const decoded = JSON.parse(atob(normalizedPayload)) as { email?: string }
    return decoded.email ?? null
  } catch {
    return null
  }
}

interface AuthContextValue {
  token: string | null
  userName: string | null
  userEmail: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [userName, setUserName] = useState<string | null>(null)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const syncProfile = useCallback(async () => {
    try {
      const profile = await getCurrentUserProfile()
      console.log('Profile fetched from API:', profile)
      
      const resolvedName = toTitleCase(profile.name.trim()) || deriveNameFromEmail(profile.email)
      const resolvedEmail = profile.email.trim().toLowerCase()

      console.log('Resolved name:', resolvedName)
      console.log('Resolved email:', resolvedEmail)

      localStorage.setItem(NAME_STORAGE_KEY, resolvedName)
      localStorage.setItem(EMAIL_STORAGE_KEY, resolvedEmail)
      setUserName(resolvedName)
      setUserEmail(resolvedEmail)
    } catch (error) {
      console.error('Failed to sync profile from database:', error)
      throw error
    }
  }, [])

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY)
      const storedEmail = localStorage.getItem(EMAIL_STORAGE_KEY)

      setToken(storedToken)
      setUserEmail(storedEmail)

      if (storedToken) {
        try {
          await syncProfile()
        } catch (error) {
          console.error('Failed to sync profile on init:', error)
          setUserName(null)
        }
      } else {
        setIsLoading(false)
      }

      setIsLoading(false)
    }

    void initializeAuth()
  }, [syncProfile])

  const login = useCallback(async (email: string, password: string) => {
    const accessToken = await loginUser(email, password)
    const tokenEmail = decodeTokenEmail(accessToken)
    const resolvedEmail = tokenEmail || email.trim().toLowerCase()

    localStorage.setItem(TOKEN_STORAGE_KEY, accessToken)
    localStorage.setItem(EMAIL_STORAGE_KEY, resolvedEmail)
    setToken(accessToken)
    setUserEmail(resolvedEmail)
    setUserName(null) // Clear name, wait for sync

    // Must fetch from database before finishing
    await syncProfile()
  }, [syncProfile])

  const signup = useCallback(async (name: string, email: string, password: string) => {
    const accessToken = await signupUser(name, email, password)
    const resolvedEmail = email.trim().toLowerCase()

    localStorage.setItem(TOKEN_STORAGE_KEY, accessToken)
    localStorage.setItem(EMAIL_STORAGE_KEY, resolvedEmail)
    setToken(accessToken)
    setUserEmail(resolvedEmail)
    setUserName(null) // Clear name, wait for sync

    // Must fetch from database before finishing
    await syncProfile()
  }, [syncProfile])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(NAME_STORAGE_KEY)
    localStorage.removeItem(EMAIL_STORAGE_KEY)
    setToken(null)
    setUserName(null)
    setUserEmail(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      userName,
      userEmail,
      isAuthenticated: Boolean(token),
      isLoading,
      login,
      signup,
      logout,
    }),
    [isLoading, login, logout, signup, token, userEmail, userName]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
