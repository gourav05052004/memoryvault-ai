'use client'

import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import MemoriesGrid from '@/components/memories/memories-grid'
import MemoryDetailModal from '@/components/memory-detail-modal'
import MemorySkeleton from '@/components/memories/memory-skeleton'
import ProtectedRoute from '@/components/auth/protected-route'
import { getMemories } from '@/lib/api'
import type { Memory } from '@/lib/api'

export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadMemories = useCallback(async () => {
    try {
      setIsLoading(true)
      const data = await getMemories()
      setMemories(data)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      toast.error(`Failed to load memories: ${errorMsg}`)
      setMemories([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMemories()
  }, [loadMemories])

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-foreground mb-2">Your Memories</h1>
            <p className="text-lg text-muted-foreground">
              Browse and manage all your saved memories
            </p>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <MemorySkeleton key={i} />
              ))}
            </div>
          ) : (
            <MemoriesGrid
              memories={memories}
              onViewDetails={setSelectedMemory}
            />
          )}
        </div>

        {selectedMemory && (
          <MemoryDetailModal
            memory={selectedMemory}
            isOpen={true}
            onClose={() => setSelectedMemory(null)}
            onMemoryDeleted={() => {
              setSelectedMemory(null)
              loadMemories()
            }}
          />
        )}
      </div>
    </ProtectedRoute>
  )
}
