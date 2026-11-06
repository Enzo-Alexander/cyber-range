import { http } from './client'

export interface BookSummary {
  id: number
  title: string
  author: string
  page_count: number
  created_at: string
}

export interface BookPage {
  id: number
  position: number
  content: string
  image: string | null
  created_at: string
}

export interface BookDetail {
  id: number
  title: string
  author: string
  created_at: string
  pages: BookPage[]
}

export function bookImageUrl(path: string | null) {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  if (path.startsWith('/api/uploads/')) return path
  if (path.startsWith('/uploads/')) return `/api${path}`
  return path
}

export const booksApi = {
  list: () => http.get<BookSummary[]>('/books'),
  get: (id: number) => http.get<BookDetail>(`/books/${id}`),
  adminList: () => http.get<BookSummary[]>('/admin/books'),
  create: (title: string) => http.post<BookDetail>('/admin/books', { title }),
  update: (id: number, title: string) =>
    http.put<BookSummary>(`/admin/books/${id}`, { title }),
  remove: (id: number) => http.delete(`/admin/books/${id}`),
  addPage: (bookId: number, body: { content: string; image: string | null; after_page_id: number | null }) =>
    http.post<BookDetail>(`/admin/books/${bookId}/pages`, body),
  updatePage: (bookId: number, pageId: number, body: { content: string; image: string | null }) =>
    http.put<BookDetail>(`/admin/books/${bookId}/pages/${pageId}`, body),
  removePage: (bookId: number, pageId: number) =>
    http.delete<BookDetail>(`/admin/books/${bookId}/pages/${pageId}`),
  uploadImage: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.postForm<{ path: string }>('/admin/books/upload-image', form)
  },
}
