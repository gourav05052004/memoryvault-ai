'use client'

import { useState, useRef } from 'react'
import { FileText, Upload, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { uploadPdf } from '@/lib/api'

export default function UploadPDFCard() {
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [title, setTitle] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      // Check by MIME type or file extension
      const isPdf = selectedFile.type === 'application/pdf' || selectedFile.name.toLowerCase().endsWith('.pdf')
      if (isPdf) {
        setFile(selectedFile)
        console.log('PDF file selected:', selectedFile.name)
      } else {
        toast.error('Please select a valid PDF file')
      }
    }
  }

  const handleUpload = async () => {
    if (!file || !title.trim()) {
      toast.error('Please select a file and enter a title')
      return
    }

    console.log('Starting upload:', { file: file.name, title })
    setIsLoading(true)
    try {
      console.log('Calling uploadPdf API...')
      await uploadPdf(file, title)
      console.log('Upload successful!')
      setIsSuccess(true)
      setTitle('')
      setFile(null)
      toast.success('PDF uploaded successfully')
      
      setTimeout(() => {
        setIsSuccess(false)
      }, 2000)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error'
      console.error('Upload error:', error)
      toast.error(`Upload failed: ${errorMsg}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="flex flex-col gap-6 p-6 border-2 hover:border-primary/50 transition-colors">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <FileText className="h-6 w-6 text-primary" />
        </div>
        <h3 className="font-semibold text-lg">Upload PDF</h3>
      </div>

      <p className="text-sm text-muted-foreground">
        Extract and store insights from PDF documents
      </p>

      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">Document Title</label>
          <Input
            placeholder="e.g., Q4 Financial Report"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isLoading || isSuccess}
            className="mt-1"
          />
        </div>

        <div className="border-2 border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
          <p className="text-sm font-medium">
            {file ? file.name : 'Click to select PDF'}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Maximum 20MB
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      </div>

      <Button
        onClick={handleUpload}
        disabled={!file || !title.trim() || isLoading || isSuccess}
        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
      >
        {isLoading ? (
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
            Uploading...
          </div>
        ) : isSuccess ? (
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Success!
          </div>
        ) : (
          'Upload PDF'
        )}
      </Button>
    </Card>
  )
}
