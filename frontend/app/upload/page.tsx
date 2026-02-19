import UploadPDFCard from '@/components/upload-cards/upload-pdf-card'
import UploadImageCard from '@/components/upload-cards/upload-image-card'
import CreateTextNoteCard from '@/components/upload-cards/create-text-note-card'

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-2">Add to Your Memory</h1>
          <p className="text-lg text-muted-foreground">
            Choose how you'd like to save your information
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <UploadPDFCard />
          <UploadImageCard />
          <CreateTextNoteCard />
        </div>
      </div>
    </div>
  )
}
