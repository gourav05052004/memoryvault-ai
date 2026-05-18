'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from 'sonner'
import MessageBubble from './message-bubble'
import MatchedMemories from './matched-memories'
import MemoryDetailModal from '@/components/memory-detail-modal'
import { askMemory } from '@/lib/api'
import type { Memory } from '@/lib/api'

interface ChatMessage {
  id: string
  message: string
  isUser: boolean
  matchedMemories?: Memory[]
}

const INITIAL_GREETING = "Hi! I'm your memory assistant powered by AI. Ask me anything about your memories, and I'll help you find relevant File related to it."

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      message: INITIAL_GREETING,
      isUser: false,
    },
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      message: inputValue,
      isUser: true,
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await askMemory(inputValue, 1)

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        message: response.answer,
        isUser: false,
        matchedMemories: response.matched_memories.length > 0 ? [response.matched_memories[0]] : [],
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get answer'
      toast.error(errorMessage)
      
      const errorAiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        message: `Sorry, I encountered an error while processing your question. Please try again.`,
        isUser: false,
      }
      setMessages((prev) => [...prev, errorAiMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-linear-to-b from-card to-card/50">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto space-y-4 p-6">
        {messages.map((msg) => (
          <div key={msg.id} className="space-y-3">
            <MessageBubble message={msg.message} isUser={msg.isUser} />
            {msg.matchedMemories && msg.matchedMemories.length > 0 && (
              <div className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
                <div className="max-w-xs lg:max-w-md w-full">
                  <MatchedMemories
                    memories={msg.matchedMemories}
                    onMemoryClick={setSelectedMemory}
                  />
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="flex gap-3 items-center px-5 py-4 bg-linear-to-r from-primary/10 to-purple-500/10 border border-primary/20 rounded-xl">
              <Loader2 className="h-4 w-4 text-primary animate-spin" />
              <span className="text-sm text-muted-foreground">AI is thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border/50 p-5 bg-linear-to-t from-card to-transparent">
        <div className="flex gap-3">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            placeholder="Ask anything about your memories..."
            disabled={isLoading}
            className="flex-1 bg-background border-border focus:border-primary focus:ring-1 focus:ring-primary/30 rounded-lg"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="bg-linear-to-r from-primary to-primary/80 hover:from-primary hover:to-primary text-primary-foreground gap-2 rounded-lg transition-all"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span className="hidden sm:inline">Send</span>
          </Button>
        </div>
      </div>

      {selectedMemory && (
        <MemoryDetailModal
          memory={selectedMemory}
          isOpen={true}
          onClose={() => setSelectedMemory(null)}
        />
      )}
    </div>
  )
}
