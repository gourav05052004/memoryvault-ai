import ChatInterface from '@/components/chat/chat-interface'
import ProtectedRoute from '@/components/auth/protected-route'

export default function AskPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background flex flex-col">
        <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8 flex-1 flex flex-col">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-foreground">Ask Your Memories</h1>
            <p className="text-muted-foreground mt-2">
              Chat with AI to explore and understand your memories
            </p>
          </div>

          <div className="flex-1 bg-card rounded-lg border border-border shadow-sm overflow-hidden flex flex-col">
            <ChatInterface />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
