const API_BASE_URL = 'http://localhost:8001'

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
  summary: string
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
  matches: Memory[]
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

async function fetchWithErrorHandling<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`
      )
    }

    return await response.json() as T
  } catch (error) {
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
    matches: BackendMemory[]
  }>(`${API_BASE_URL}/ask`, {
    method: 'POST',
    body: JSON.stringify({ question, top_k: topK }),
  })
  return {
    answer: response.answer,
    matches: response.matches.map(transformBackendMemory),
  }
}

export async function deleteMemory(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/memory/${id}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(
      errorData.detail || `Failed to delete memory: ${response.statusText}`
    )
  }
}
