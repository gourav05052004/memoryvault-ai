'use client'

import { FileText, Image as ImageIcon, MessageSquare } from 'lucide-react'
import { Card } from '@/components/ui/card'
import type { Memory } from '@/lib/api'

interface MatchedMemoriesProps {
  memories: Memory[]
}

export default function MatchedMemories({ memories }: MatchedMemoriesProps) {
  if (memories.length === 0) return null

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FileText className="h-4 w-4" />
      case 'image':
        return <ImageIcon className="h-4 w-4" />
      case 'note':
        return <MessageSquare className="h-4 w-4" />
    }
  }

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'pdf':
        return 'bg-primary/10 text-primary'
      case 'image':
        return 'bg-accent/10 text-accent'
      case 'note':
        return 'bg-secondary/10 text-secondary'
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-muted-foreground uppercase">
        Relevant Memories
      </p>
      <div className="space-y-2">
        {memories.map((memory) => (
          <Card
            key={memory.id}
            className="p-3 bg-muted/50 border-border hover:bg-muted transition-colors cursor-pointer"
          >
            <div className="flex items-start gap-2">
              <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${getTypeBadgeColor(memory.type)}`}>
                {getTypeIcon(memory.type)}
                {memory.type.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">
                  {memory.title}
                </p>
                <p className="text-xs text-muted-foreground line-clamp-1 mt-1">
                  {memory.summary}
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
