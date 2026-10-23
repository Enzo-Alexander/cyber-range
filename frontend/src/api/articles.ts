import { http } from './client'

export type ArticleType = 'article' | 'announcement'

export interface Article {
  id: number
  title: string
  content: string
  type: ArticleType
  author: string
  created_at: string
}

export const articlesApi = {
  list: (type?: ArticleType) =>
    http.get<Article[]>(type ? `/articles?type=${type}` : '/articles'),
  get: (id: number) => http.get<Article>(`/articles/${id}`),
  create: (body: { title: string; content: string; type: ArticleType }) =>
    http.post<Article>('/admin/articles', body),
  remove: (id: number) => http.delete(`/admin/articles/${id}`),
  parseDoc: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.postForm<{ suggested_title: string; content: string; images: string[] }>(
      '/admin/parse-doc',
      fd,
    )
  },
}
