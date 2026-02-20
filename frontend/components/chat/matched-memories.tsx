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
        return 'bg-blue-500/10 text-blue-700 border border-blue-200/30'
      case 'image':
        return 'bg-purple-500/10 text-purple-700 border border-purple-200/30'
      case 'note':
        return 'bg-amber-500/10 text-amber-700 border border-amber-200/30'
      default:
        return 'bg-primary/10 text-primary'
    }
  }

  const handleOpenDocument = (memory: Memory) => {
    if (memory.fileUrl) {
      window.open(memory.fileUrl, '_blank')
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="h-1 w-1 rounded-full bg-primary" />
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Related Memory
        </p>
      </div>
      <div className="space-y-2">
        {memories.map((memory) => (
          <Card
            key={memory.id}
            className="p-4 bg-linear-to-br from-card/80 to-muted/30 border border-border hover:border-primary/50 hover:shadow-md transition-all duration-200 cursor-pointer group"
            onClick={() => handleOpenDocument(memory)}
          >
            <div className="flex items-start gap-3">
              <div className={`flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-semibold shrink-0 ${getTypeBadgeColor(memory.type)}`}>
                {getTypeIcon(memory.type)}
                <span>{memory.type.toUpperCase()}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                  {memory.title}
                </p>
                {memory.fileName && (
                  <p className="text-xs text-muted-foreground truncate mt-1.5">
                    📄 {memory.fileName}
                  </p>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
