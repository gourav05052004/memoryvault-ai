'use client'

import { useState, useMemo } from 'react'
import MemoryCard from './memory-card'
import SearchFilterBar from './search-filter-bar'
import type { Memory } from '@/lib/api'

interface MemoriesGridProps {
  memories: Memory[]
  onViewDetails: (memory: Memory) => void
}

export default function MemoriesGrid({ memories, onViewDetails }: MemoriesGridProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<'all' | 'pdf' | 'image' | 'note'>('all')

  const filteredMemories = useMemo(() => {
    return memories.filter((memory) => {
      const query = searchQuery.toLowerCase().trim()
      
      if (!query && filterType === 'all') {
        return true
      }

      const matchesFilter = filterType === 'all' || memory.type === filterType
      
      if (!query) {
        return matchesFilter
      }

      // Enhanced search: title, individual tags, and extracted text
      const matchesTitle = memory.title.toLowerCase().includes(query)
      const matchesTags = memory.tags.some((tag) =>
        tag.toLowerCase().includes(query)
      )
      const matchesContent = memory.extractedText?.toLowerCase().includes(query)

      return (matchesTitle || matchesTags || matchesContent) && matchesFilter
    })
  }, [memories, searchQuery, filterType])

  return (
    <div className="space-y-6">
      <SearchFilterBar
        onSearchChange={setSearchQuery}
        onFilterChange={setFilterType}
      />

      {filteredMemories.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground text-lg">
            {searchQuery || filterType !== 'all'
              ? 'No memories found. Try adjusting your search or filters.'
              : 'No memories yet. Start by uploading your first memory!'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMemories.map((memory) => (
            <MemoryCard
              key={memory.id}
              memory={memory}
              onViewDetails={onViewDetails}
            />
          ))}
        </div>
      )}
    </div>
  )
}
