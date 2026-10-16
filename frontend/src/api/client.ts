const API = (import.meta.env.VITE_API_BASE as string | undefined) || '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('cr_token')
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(`${API}${path}`, { ...options, headers })

  if (!res.ok) {
    let detail = '请求失败'
    try {
      const data = await res.json()
      if (data && data.detail) detail = data.detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export const http = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  postForm: <T>(path: string, body: FormData) =>
    request<T>(path, { method: 'POST', body }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path: string, body?: unknown) =>
    request<void>(path, { method: 'DELETE', body: body ? JSON.stringify(body) : undefined }),
}
