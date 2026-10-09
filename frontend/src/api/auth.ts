import { http } from './client'

export interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
}

export const authApi = {
  login: (username: string, password: string) =>
    http.post<Token>('/auth/login', { username, password }),
  register: (username: string, email: string, password: string) =>
    http.post<User>('/auth/register', { username, email, password }),
  me: () => http.get<User>('/users/me'),
}
