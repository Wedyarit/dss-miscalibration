"use client"

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'

interface FileUploaderProps {
  onUpload: (file: File) => void
  accept?: string
  maxSize?: number // in MB
  isLoading?: boolean
}

export function FileUploader({ 
  onUpload, 
  accept = ".csv,.json", 
  maxSize = 10,
  isLoading = false 
}: FileUploaderProps) {
  const [dragActive, setDragActive] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file: File) => {
    setError(null)
    
    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      setError(`File size must be less than ${maxSize}MB`)
      return
    }
    
    // Check file type
    const acceptedTypes = accept.split(',').map(type => type.trim())
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!acceptedTypes.includes(fileExtension)) {
      setError(`File type must be one of: ${acceptedTypes.join(', ')}`)
      return
    }
    
    onUpload(file)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload File</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-primary bg-primary/5' 
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="space-y-4">
            <div className="text-4xl">📁</div>
            <div>
              <p className="text-lg font-medium">
                Drag and drop your file here
              </p>
              <p className="text-sm text-muted-foreground">
                or click to browse
              </p>
            </div>
            
            <Input
              type="file"
              accept={accept}
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
            />
            
            <Button
              variant="outline"
              onClick={() => document.getElementById('file-upload')?.click()}
              disabled={isLoading}
            >
              {isLoading ? 'Uploading...' : 'Choose File'}
            </Button>
            
            <p className="text-xs text-muted-foreground">
              Accepted formats: {accept} (max {maxSize}MB)
            </p>
            
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
