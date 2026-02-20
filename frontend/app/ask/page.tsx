import ChatInterface from '@/components/chat/chat-interface'
import ProtectedRoute from '@/components/auth/protected-route'
import { MessageSquare } from 'lucide-react'

export default function AskPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-linear-to-br from-background via-background to-purple-950/10">
        <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
          {/* Header Section */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <MessageSquare className="h-6 w-6 text-primary" />
              </div>
              <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-linear-to-r from-foreground to-foreground/70">
                Ask Your Memories
              </h1>
            </div>
            <p className="text-lg text-muted-foreground ml-11">
              Chat with AI to explore, understand, and discover insights from your memories
            </p>
          </div>

          {/* Main Chat Area */}
          <div className="h-96 lg:h-screen max-h-[600px] bg-card border border-border shadow-lg overflow-hidden flex flex-col">
            <ChatInterface />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
