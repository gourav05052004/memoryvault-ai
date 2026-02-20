'use client'

interface MessageBubbleProps {
  message: string
  isUser: boolean
}

export default function MessageBubble({ message, isUser }: MessageBubbleProps) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs lg:max-w-md px-5 py-3 rounded-2xl text-sm leading-relaxed wrap-break-word transition-all duration-200 ${
          isUser
            ? 'bg-linear-to-br from-primary to-primary/80 text-primary-foreground rounded-br-none shadow-md hover:shadow-lg'
            : 'bg-linear-to-br from-muted to-muted/50 text-foreground border border-border/50 rounded-bl-none'
        }`}
      >
        <p>{message}</p>
      </div>
    </div>
  )
}
