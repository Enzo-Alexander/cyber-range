import { http } from './client'

export interface Article {
  id: number
  title: string
  content: string
  type: 'article' | 'announcement'
  author: string
  created_at: string
}

export const articlesApi = {
  list: () => http.get<Article[]>('/articles'),
  get: (id: number) => http.get<Article>(`/articles/${id}`),
  create: (body: { title: string; content: string; type: 'article' | 'announcement' }) =>
    http.post<Article>('/admin/articles', body),
  parseDoc: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.postForm<{ suggested_title: string; content: string; images: string[] }>(
      '/admin/parse-doc',
      fd,
    )
  },
}
