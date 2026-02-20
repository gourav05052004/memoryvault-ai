'use client'

import { FileText, Image as ImageIcon, MessageSquare, Eye } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { Memory } from '@/lib/api'

interface MemoryCardProps {
  memory: Memory
  onViewDetails: (memory: Memory) => void
}

export default function MemoryCard({ memory, onViewDetails }: MemoryCardProps) {
  const getTypeIcon = () => {
    switch (memory.type) {
      case 'pdf':
        return <FileText className="h-5 w-5" />
      case 'image':
        return <ImageIcon className="h-5 w-5" />
      case 'note':
        return <MessageSquare className="h-5 w-5" />
    }
  }

  const getTypeLabel = () => {
    return memory.type.toUpperCase()
  }

  const getTypeBadgeColor = () => {
    switch (memory.type) {
      case 'pdf':
        return 'bg-primary/10 text-primary'
      case 'image':
        return 'bg-accent/10 text-accent'
      case 'note':
        return 'bg-secondary/10 text-secondary'
    }
  }

  return (
    <Card className="flex flex-col gap-4 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <h3 className="font-semibold text-base line-clamp-2 text-foreground">
            {memory.title}
          </h3>
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getTypeBadgeColor()}`}>
          {getTypeIcon()}
          {getTypeLabel()}
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {memory.tags.map((tag) => (
          <span
            key={tag}
            className="px-2 py-1 rounded-full bg-accent/15 text-accent text-xs font-medium"
          >
            {tag}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-border">
        <span className="text-xs text-muted-foreground">
          {memory.createdAt.toLocaleDateString()}
        </span>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onViewDetails(memory)}
          className="text-primary hover:bg-primary/10"
        >
          {memory.fileUrl && (memory.type === 'pdf' || memory.type === 'image') && (
            <Eye className="h-3 w-3 mr-1" />
          )}
          View Details
        </Button>
      </div>
    </Card>
  )
}
