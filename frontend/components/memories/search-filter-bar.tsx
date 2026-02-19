'use client'

import { useState } from 'react'
import { Search, Filter } from 'lucide-react'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface SearchFilterBarProps {
  onSearchChange: (query: string) => void
  onFilterChange: (filter: 'all' | 'pdf' | 'image' | 'note') => void
}

export default function SearchFilterBar({
  onSearchChange,
  onFilterChange,
}: SearchFilterBarProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterValue, setFilterValue] = useState('all')

  const handleSearchChange = (value: string) => {
    setSearchQuery(value)
    onSearchChange(value)
  }

  const handleFilterChange = (value: string) => {
    setFilterValue(value)
    onFilterChange(value as 'all' | 'pdf' | 'image' | 'note')
  }

  return (
    <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search memories..."
          value={searchQuery}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="pl-10"
        />
      </div>

      <div className="flex items-center gap-2 min-w-fit">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <Select value={filterValue} onValueChange={handleFilterChange}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Memories</SelectItem>
            <SelectItem value="pdf">PDF Documents</SelectItem>
            <SelectItem value="image">Images</SelectItem>
            <SelectItem value="note">Notes</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
