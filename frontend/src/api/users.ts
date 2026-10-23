import { http } from './client'
import type { User } from './auth'

export const usersApi = {
  updateAccount: (email: string) =>
    http.patch<User>('/users/me/account', { email }),
  changePassword: (currentPassword: string, newPassword: string) =>
    http.post<{ success: boolean }>('/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
}
