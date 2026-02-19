export interface Memory {
  id: string
  title: string
  type: 'pdf' | 'image' | 'note'
  summary: string
  tags: string[]
  createdAt: Date
}

export const mockMemories: Memory[] = [
  {
    id: '1',
    title: 'Q4 Financial Report',
    type: 'pdf',
    summary: 'Comprehensive financial analysis and quarterly performance metrics for Q4 2024...',
    tags: ['finance', 'quarterly', 'report'],
    createdAt: new Date('2024-01-15'),
  },
  {
    id: '2',
    title: 'Team Meeting Notes',
    type: 'image',
    summary: 'Whiteboard photos from the team sync meeting discussing roadmap priorities...',
    tags: ['meeting', 'team', 'roadmap'],
    createdAt: new Date('2024-01-14'),
  },
  {
    id: '3',
    title: 'Project Ideas',
    type: 'note',
    summary: 'Brainstorm ideas for upcoming projects including AI integration and performance optimization...',
    tags: ['projects', 'ideas', 'ai'],
    createdAt: new Date('2024-01-13'),
  },
  {
    id: '4',
    title: 'Design System Spec',
    type: 'pdf',
    summary: 'Complete design system documentation with component guidelines and color specifications...',
    tags: ['design', 'documentation', 'system'],
    createdAt: new Date('2024-01-12'),
  },
  {
    id: '5',
    title: 'Conference Notes 2024',
    type: 'image',
    summary: 'Photos and notes from the annual technology conference covering industry trends...',
    tags: ['conference', 'trends', 'technology'],
    createdAt: new Date('2024-01-11'),
  },
  {
    id: '6',
    title: 'Client Requirements',
    type: 'note',
    summary: 'Detailed requirements and specifications for the new client project deliverables...',
    tags: ['client', 'requirements', 'project'],
    createdAt: new Date('2024-01-10'),
  },
  {
    id: '7',
    title: 'Market Research',
    type: 'pdf',
    summary: 'Competitive analysis and market research findings for strategic planning...',
    tags: ['market', 'research', 'strategy'],
    createdAt: new Date('2024-01-09'),
  },
  {
    id: '8',
    title: 'Technical Architecture',
    type: 'image',
    summary: 'System architecture diagram showing microservices and integration points...',
    tags: ['architecture', 'technical', 'system'],
    createdAt: new Date('2024-01-08'),
  },
  {
    id: '9',
    title: 'Personal Goals 2024',
    type: 'note',
    summary: 'Annual goals and milestones for professional development and career growth...',
    tags: ['goals', 'personal', 'development'],
    createdAt: new Date('2024-01-07'),
  },
]
