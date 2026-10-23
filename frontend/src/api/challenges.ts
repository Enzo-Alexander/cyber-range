import { http } from './client'

export interface ChallengeCard {
  id: number
  title: string
  category: string
  difficulty: number
  points: number
  status: string
  solved_count: number
  solved_by_me: boolean
}

export interface Challenge {
  id: number
  title: string
  category: string
  difficulty: number
  points: number
  description: string
  attachment: string | null
  author: string
  status: string
  solved_count: number
  created_at: string
  favorited_by_me: boolean
}

export interface FavoriteChallenge extends ChallengeCard {
  favorited_at: string
}

export interface FavoriteState {
  favorited: boolean
}

export interface AdminChallenge extends Challenge {
  flag: string
}

export interface ChallengeSubmitInput {
  title: string
  category: string
  difficulty: number
  points: number
  description: string
  attachment: string | null
  flag: string
}

export interface SolveResult {
  success: boolean
  message: string
  points: number
}

export interface Solver {
  username: string
  solved_at: string
}

export interface LeaderboardEntry {
  rank: number
  username: string
  total_points: number
  solved_count: number
  last_solved_at: string | null
}

export interface CategoryProgress {
  category: string
  percent: number
}

export interface DailyActivity {
  day: number
  count: number
}

export interface MonthlyActivity {
  year: number
  month: number
  days: number
  total: number
  active_days: number
  daily: DailyActivity[]
}

export interface YearlyMonthActivity {
  month: number
  days: number
  total: number
  daily: DailyActivity[]
}

export interface YearlyActivity {
  year: number
  total: number
  active_days: number
  months: YearlyMonthActivity[]
}

export interface ProfileSolve {
  challenge_id: number
  title: string
  category: string
  points: number
  solved_at: string
}

export interface Profile {
  user: {
    id: number
    username: string
    email: string
    role: string
    created_at: string
  }
  total_points: number
  total_solved: number
  competition_solved: number
  level: number
  level_progress: number
  level_required: number
  rank: number
  progress: CategoryProgress[]
  solves: ProfileSolve[]
}

export interface AdminStats {
  challenge_total: number
  pending: number
  today: number
  user_total: number
}

export const CATEGORIES = ['全部', '逆向工程', '二进制漏洞', '密码学', 'Web安全', '流量分析', '数字取证']

export const challengesApi = {
  list: (category?: string, search?: string) => {
    const p = new URLSearchParams()
    if (category && category !== '全部') p.set('category', category)
    if (search) p.set('search', search)
    const qs = p.toString()
    return http.get<ChallengeCard[]>(`/challenges${qs ? `?${qs}` : ''}`)
  },
  get: (id: number) => http.get<Challenge>(`/challenges/${id}`),
  solvers: (id: number) => http.get<Solver[]>(`/challenges/${id}/solvers`),
  related: (id: number) => http.get<ChallengeCard[]>(`/challenges/${id}/related`),
  submit: (id: number, flag: string) => http.post<SolveResult>(`/challenges/${id}/submit`, { flag }),
  submitChallenge: (body: ChallengeSubmitInput) =>
    http.post<Challenge>('/challenges/submit', body),
  toggleFavorite: (id: number) =>
    http.post<FavoriteState>(`/users/me/favorites/${id}/toggle`, {}),
  favorites: () => http.get<FavoriteChallenge[]>('/users/me/favorites'),
  monthlyActivity: (year: number, month: number) =>
    http.get<MonthlyActivity>(`/users/me/activity/monthly?year=${year}&month=${month}`),
  yearlyActivity: (year: number) =>
    http.get<YearlyActivity>(`/users/me/activity/yearly?year=${year}`),
  leaderboard: () => http.get<LeaderboardEntry[]>('/challenges/leaderboard'),
  profile: () => http.get<Profile>('/users/me/profile'),
  adminList: (status?: string) =>
    http.get<AdminChallenge[]>(`/admin/challenges${status ? `?status=${status}` : ''}`),
  adminStats: () => http.get<AdminStats>('/admin/stats'),
  adminCreate: (body: Partial<Challenge> & { flag: string }) =>
    http.post<AdminChallenge>('/admin/challenges', body),
  adminUpdate: (id: number, body: Partial<Challenge>) =>
    http.put<AdminChallenge>(`/admin/challenges/${id}`, body),
  adminDelete: (id: number) => http.delete(`/admin/challenges/${id}`),
  uploadAttachment: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.postForm<{ filename: string; original: string }>('/admin/attachments', fd)
  },
  uploadSubmissionAttachment: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.postForm<{ filename: string; original: string }>('/challenges/attachments', fd)
  },
  adminAttachmentUrl: (id: number) => `/api/admin/challenges/${id}/attachment`,
}
