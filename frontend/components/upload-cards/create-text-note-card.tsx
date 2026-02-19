'use client'

import { useState } from 'react'
import { FileText, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { createNote } from '@/lib/api'

export default function CreateTextNoteCard() {
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  const handleSave = async () => {
    if (!title.trim() || !content.trim()) {
      toast.error('Please enter both title and content')
      return
    }

    console.log('Creating note:', { title })
    setIsLoading(true)
    try {
      console.log('Calling createNote API...')
      await createNote(title, content)
      console.log('Note created successfully!')
      setIsSuccess(true)
      setTitle('')
      setContent('')
      toast.success('Note created successfully')
      
      setTimeout(() => {
        setIsSuccess(false)
      }, 2000)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      console.error('Note creation error:', error)
      toast.error(`Failed to create note: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="flex flex-col gap-6 p-6 border-2 hover:border-primary/50 transition-colors">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-secondary/10 rounded-lg">
          <FileText className="h-6 w-6 text-secondary" />
        </div>
        <h3 className="font-semibold text-lg">Create Text Note</h3>
      </div>

      <p className="text-sm text-muted-foreground">
        Write and save important notes directly
      </p>

      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">Note Title</label>
          <Input
            placeholder="e.g., Project Ideas"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isLoading || isSuccess}
            className="mt-1"
          />
        </div>

        <div>
          <label className="text-sm font-medium">Note Content</label>
          <Textarea
            placeholder="Write your note here..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            disabled={isLoading || isSuccess}
            className="mt-1 min-h-32 resize-none"
          />
        </div>
      </div>

      <Button
        onClick={handleSave}
        disabled={!title.trim() || !content.trim() || isLoading || isSuccess}
        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
      >
        {isLoading ? (
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
            Saving...
          </div>
        ) : isSuccess ? (
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Saved!
          </div>
        ) : (
          'Save Note'
        )}
      </Button>
    </Card>
  )
}
