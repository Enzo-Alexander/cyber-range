import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi, type User } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('cr_token'))
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    token.value = res.access_token
    localStorage.setItem('cr_token', res.access_token)
    user.value = await authApi.me()
  }

  async function register(username: string, email: string, password: string) {
    await authApi.register(username, email, password)
    await login(username, password)
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      user.value = await authApi.me()
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('cr_token')
  }

  return { token, user, isAuthenticated, login, register, fetchMe, logout }
})
