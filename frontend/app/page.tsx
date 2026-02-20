import Link from 'next/link'
import { Brain, ShieldCheck, Sparkles, Database, MessageSquareText, FileText } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const features = [
  {
    title: 'Secure Multi-User Workspace',
    description: 'JWT authentication with user-level data isolation keeps every memory private by default.',
    icon: ShieldCheck,
  },
  {
    title: 'Smart Memory Ingestion',
    description: 'Upload PDFs, images, or text notes and automatically generate summaries and tags.',
    icon: FileText,
  },
  {
    title: 'Semantic Memory Retrieval',
    description: 'ChromaDB-powered embeddings help surface the most relevant memories instantly.',
    icon: Database,
  },
  {
    title: 'Conversational Recall',
    description: 'Ask natural-language questions and get grounded answers from your own memory vault.',
    icon: MessageSquareText,
  },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4 text-primary" />
            AI-powered memory management for teams and individuals
          </div>

          <h1 className="text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Build your second brain with MemoryVault AI
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg text-muted-foreground">
            Capture documents, images, and notes in one place, then retrieve what matters through fast semantic search and conversational Q&A.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" asChild>
              <Link href="/signup">Get Started</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/login">Login</Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center gap-2 text-foreground">
          <Brain className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold">Why MemoryVault AI</h2>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <Card key={feature.title} className="border border-border bg-card p-6">
                <div className="mb-4 inline-flex rounded-lg bg-primary/10 p-2">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">{feature.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{feature.description}</p>
              </Card>
            )
          })}
        </div>
      </section>

      <section className="border-t border-border bg-card/40">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-12 text-center sm:px-6 md:flex-row md:text-left lg:px-8">
          <div>
            <h3 className="text-2xl font-semibold text-foreground">Ready to organize your knowledge?</h3>
            <p className="mt-1 text-muted-foreground">Create an account and start building your searchable memory vault today.</p>
          </div>
          <Button size="lg" asChild>
            <Link href="/signup">Create Free Account</Link>
          </Button>
        </div>
      </section>
    </div>
  )
}
