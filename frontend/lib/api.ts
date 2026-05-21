const API_BASE_URL = '/api'

const TOKEN_STORAGE_KEY = 'memoryvault_token'

export interface UploadResponse {
  id: string
  extractedTextLength: number
  message: string
  summary: string
  tags: string[]
}

interface BackendMemory {
  _id: string
  type: 'pdf' | 'image' | 'note'
  title: string
  summary: string
  tags: string[]
  fileName?: string
  fileUrl?: string
  fileType?: string
  fileSize?: number
  extractedText?: string
  createdAt: string
  updatedAt?: string
}

export interface Memory {
  id: string
  type: 'pdf' | 'image' | 'note'
  title: string
  summary?: string
  tags: string[]
  fileName?: string
  fileUrl?: string
  fileType?: string
  fileSize?: number
  extractedText?: string
  createdAt: Date
  updatedAt?: string
}

export interface AskResponse {
  answer: string
  matched_memories: Memory[]
}

interface AuthResponse {
  access_token: string
  token_type: string
}

interface MessageResponse {
  message: string
}

export interface UserProfile {
  id: string
  name: string
  email: string
}

function getAuthToken(): string | null {
  if (typeof window === 'undefined') {
    return null
  }
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

function getAuthHeaders(): HeadersInit {
  const token = getAuthToken()
  if (!token) {
    return {}
  }
  return {
    Authorization: `Bearer ${token}`,
  }
}

function transformBackendMemory(backend: BackendMemory): Memory {
  return {
    id: backend._id,
    type: backend.type,
    title: backend.title,
    summary: backend.summary,
    tags: backend.tags,
    fileName: backend.fileName,
    fileUrl: backend.fileUrl,
    fileType: backend.fileType,
    fileSize: backend.fileSize,
    extractedText: backend.extractedText,
    createdAt: new Date(backend.createdAt),
    updatedAt: backend.updatedAt,
  }
}

async function readResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || ''
  const rawBody = await response.text()

  if (!rawBody) {
    return null
  }

  if (contentType.includes('application/json')) {
    return JSON.parse(rawBody)
  }

  try {
    return JSON.parse(rawBody)
  } catch {
    return rawBody
  }
}

async function fetchWithErrorHandling<T>(
  url: string,
  options: RequestInit = {},
  config: { suppressErrorLog?: boolean } = {}
): Promise<T> {
  try {
    const token = getAuthToken()
    console.log('Making request to:', url)
    console.log('Auth token present:', !!token)
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers,
      },
    })

    console.log('Response status:', response.status)
    const data = await readResponseBody(response)
    console.log('Response data:', data)

    if (!response.ok) {
      const errorDetail =
        data && typeof data === 'object' && 'detail' in data
          ? String((data as { detail?: unknown }).detail ?? '')
          : data && typeof data === 'object' && 'message' in data
            ? String((data as { message?: unknown }).message ?? '')
            : typeof data === 'string'
              ? data
              : ''

      if (!config.suppressErrorLog) {
        console.error('Response error:', {
          status: response.status,
          statusText: response.statusText,
          detail: errorDetail || data,
        })
      }
      throw new Error(
        errorDetail || `HTTP ${response.status}: ${response.statusText}`
      )
    }

    return data as T
  } catch (error) {
    if (!config.suppressErrorLog) {
      console.error('Fetch error:', error)
    }
    throw error instanceof Error ? error : new Error('Unknown error occurred')
  }
}

export async function uploadPdf(file: File, title?: string): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (title) {
    formData.append('title', title)
  }

  const response = await fetch(`${API_BASE_URL}/upload/pdf`, {
    method: 'POST',
    body: formData,
    headers: {
      ...getAuthHeaders(),
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(
      errorData.detail || `Failed to upload PDF: ${response.statusText}`
    )
  }

  return await response.json() as UploadResponse
}

export async function uploadImage(file: File, title?: string): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (title) {
    formData.append('title', title)
  }

  const response = await fetch(`${API_BASE_URL}/upload/image`, {
    method: 'POST',
    body: formData,
    headers: {
      ...getAuthHeaders(),
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(
      errorData.detail || `Failed to upload image: ${response.statusText}`
    )
  }

  return await response.json() as UploadResponse
}

export async function createNote(
  title: string,
  content: string
): Promise<UploadResponse> {
  return fetchWithErrorHandling<UploadResponse>(
    `${API_BASE_URL}/memory/note`,
    {
      method: 'POST',
      body: JSON.stringify({ title, content }),
    }
  )
}

export async function getMemories(): Promise<Memory[]> {
  const backendMemories = await fetchWithErrorHandling<BackendMemory[]>(
    `${API_BASE_URL}/memories`
  )
  return backendMemories.map(transformBackendMemory)
}

export async function getMemoryById(id: string): Promise<Memory> {
  const backendMemory = await fetchWithErrorHandling<BackendMemory>(
    `${API_BASE_URL}/memory/${id}`
  )
  return transformBackendMemory(backendMemory)
}

export async function askMemory(
  question: string,
  topK: number = 3
): Promise<AskResponse> {
  const response = await fetchWithErrorHandling<{
    answer: string
    matched_memories: BackendMemory[]
  }>(`${API_BASE_URL}/ask`, {
    method: 'POST',
    body: JSON.stringify({ question, top_k: topK }),
  })
  return {
    answer: response.answer,
    matched_memories: response.matched_memories.map(transformBackendMemory),
  }
}

export async function deleteMemory(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/memory/${id}`, {
    method: 'DELETE',
    headers: {
      ...getAuthHeaders(),
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(
      errorData.detail || `Failed to delete memory: ${response.statusText}`
    )
  }
}

export async function signupUser(
  name: string,
  email: string,
  password: string
): Promise<string> {
  const response = await fetchWithErrorHandling<AuthResponse>(
    `${API_BASE_URL}/auth/signup`,
    {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }
  )
  return response.access_token
}

export async function loginUser(email: string, password: string): Promise<string> {
  const response = await fetchWithErrorHandling<AuthResponse>(
    `${API_BASE_URL}/auth/login`,
    {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }
  )
  return response.access_token
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<string> {
  const response = await fetchWithErrorHandling<MessageResponse>(
    `${API_BASE_URL}/auth/change-password`,
    {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    }
  )

  return response.message
}

export async function getCurrentUserProfile(): Promise<UserProfile> {
  return fetchWithErrorHandling<UserProfile>(
    `${API_BASE_URL}/auth/me`,
    {},
    { suppressErrorLog: true }
  )
}
