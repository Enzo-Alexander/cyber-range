import { http } from './client'

export interface NotificationItem {
  id: number
  type: string
  title: string
  content: string
  related_challenge_id: number | null
  related_article_id: number | null
  is_read: boolean
  created_at: string
}

export const notificationsApi = {
  list: () => http.get<NotificationItem[]>('/notifications'),
  markRead: (id: number) => http.post<{ success: boolean }>(`/notifications/${id}/read`, {}),
  markAllRead: () => http.post<{ success: boolean }>('/notifications/read-all', {}),
}
