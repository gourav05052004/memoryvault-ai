'use client'

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from 'sonner'
import MessageBubble from './message-bubble'
import MatchedMemories from './matched-memories'
import { askMemory } from '@/lib/api'
import type { Memory } from '@/lib/api'

interface ChatMessage {
  id: string
  message: string
  isUser: boolean
  matchedMemories?: Memory[]
}

const INITIAL_GREETING = "Hi! I'm your AI memory assistant. Ask me anything about your memories, and I'll help you find relevant information and insights."

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
      const response = await askMemory(inputValue, 3)

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        message: response.answer,
        isUser: false,
        matchedMemories: response.matches,
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get answer'
      toast.error(errorMessage)
      
      const errorAiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        message: `Sorry, I encountered an error while processing your question: ${errorMessage}. Please try again.`,
        isUser: false,
      }
      setMessages((prev) => [...prev, errorAiMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg) => (
          <div key={msg.id} className="space-y-3">
            <MessageBubble message={msg.message} isUser={msg.isUser} />
            {msg.matchedMemories && msg.matchedMemories.length > 0 && (
              <div className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
                <div className="max-w-xs lg:max-w-md w-full">
                  <MatchedMemories memories={msg.matchedMemories} />
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="flex gap-2 items-center px-4 py-3 bg-muted rounded-lg">
              <div className="flex gap-1">
                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" />
                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border p-4 bg-card">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            placeholder="Ask me about your memories..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2"
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline">Send</span>
          </Button>
        </div>
      </div>
    </div>
  )
}
