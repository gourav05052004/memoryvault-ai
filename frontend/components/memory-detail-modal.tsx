'use client'

import { useState, useEffect } from 'react'
import { X, FileText, Image as ImageIcon, MessageSquare, Trash2, ExternalLink } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { deleteMemory } from '@/lib/api'
import type { Memory } from '@/lib/api'

interface MemoryDetailModalProps {
  memory: Memory
  isOpen: boolean
  onClose: () => void
  onMemoryDeleted?: () => void
}

export default function MemoryDetailModal({
  memory,
  isOpen,
  onClose,
  onMemoryDeleted,
}: MemoryDetailModalProps) {
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  const handleDelete = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${memory.title}"? This action cannot be undone.`
    )

    if (!confirmed) return

    setIsDeleting(true)
    try {
      await deleteMemory(memory.id)
      toast.success('Memory deleted successfully')
      onMemoryDeleted?.()
      onClose()
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to delete memory'
      toast.error(errorMsg)
      console.error('Delete error:', error)
    } finally {
      setIsDeleting(false)
    }
  }

  if (!isOpen) return null

  const getTypeIcon = () => {
    switch (memory.type) {
      case 'pdf':
        return <FileText className="h-6 w-6" />
      case 'image':
        return <ImageIcon className="h-6 w-6" />
      case 'note':
        return <MessageSquare className="h-6 w-6" />
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
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 cursor-pointer"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-card rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 flex items-center justify-between p-6 border-b border-border bg-card">
            <div className="flex items-center gap-3">
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getTypeBadgeColor()}`}>
                {getTypeIcon()}
                {getTypeLabel()}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-muted rounded-lg transition-colors"
              aria-label="Close modal"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Title */}
            <div>
              <h1 className="text-3xl font-bold text-foreground text-balance">
                {memory.title}
              </h1>
            </div>

            {/* File Preview */}
            {memory.fileUrl && (
              <div className="space-y-3">
                {memory.type === 'image' ? (
                  <Button
                    onClick={() => window.open(memory.fileUrl, '_blank')}
                    className="w-full gap-2"
                    variant="outline"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Open Image in New Tab
                  </Button>
                ) : memory.type === 'pdf' ? (
                  <Button
                    onClick={() => window.open(memory.fileUrl, '_blank')}
                    className="w-full gap-2"
                    variant="outline"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Open PDF in New Tab
                  </Button>
                ) : null}
              </div>
            )}

            {/* Note Content */}
            {memory.type === 'note' && memory.extractedText && (
              <div>
                <p className="text-muted-foreground font-medium text-sm mb-2">Note Content</p>
                <div className="rounded-lg border border-border bg-muted/30 p-4">
                  <p className="text-foreground whitespace-pre-wrap wrap-break-word leading-relaxed">
                    {memory.extractedText}
                  </p>
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground font-medium">Created</p>
                <p className="text-foreground mt-1">
                  {memory.createdAt.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground font-medium">Type</p>
                <p className="text-foreground mt-1 capitalize">{memory.type}</p>
              </div>
              {memory.fileName && (
                <div>
                  <p className="text-muted-foreground font-medium">File Name</p>
                  <p className="text-foreground mt-1 truncate" title={memory.fileName}>
                    {memory.fileName}
                  </p>
                </div>
              )}
              {memory.fileSize && (
                <div>
                  <p className="text-muted-foreground font-medium">File Size</p>
                  <p className="text-foreground mt-1">
                    {(memory.fileSize / 1024).toFixed(2)} KB
                  </p>
                </div>
              )}
            </div>

            {/* Tags */}
            {memory.tags.length > 0 && (
              <div>
                <p className="text-muted-foreground font-medium text-sm mb-2">Tags</p>
                <div className="flex flex-wrap gap-2">
                  {memory.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-3 py-1 rounded-full bg-accent/15 text-accent text-sm font-medium"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t border-border">
              <Button
                onClick={handleDelete}
                disabled={isDeleting}
                variant="destructive"
                className="flex-1 gap-2"
              >
                {isDeleting ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
