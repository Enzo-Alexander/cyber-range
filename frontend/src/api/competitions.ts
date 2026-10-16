import { http } from './client'

export interface Competition {
  id: number
  name: string
  description: string
  icon: string
  created_at: string
}

export interface CompetitionEdition {
  id: number
  competition_id: number
  name: string
  year: number
  created_at: string
  /** 当前用户在该届比赛里已获得的分数 */
  my_points: number
}

export interface CompetitionChallenge {
  id: number
  edition_id: number
  title: string
  category: string
  difficulty: number
  description: string
  points: number
  solved_count: number
  solved_by_me: boolean
  attachment?: string | null
  created_at: string
}

export interface CompetitionChallengeDetail {
  id: number
  edition_id: number
  title: string
  category: string
  difficulty: number
  description: string
  points: number
  solved_count: number
  solved_by_me: boolean
  attachment: string | null
  created_at: string
  competition_id: number
  competition_name: string
  competition_icon: string
  edition_name: string
  edition_year: number
}

export const competitionsApi = {
  list: () => http.get<Competition[]>('/competitions'),
  editions: (cid: number) => http.get<CompetitionEdition[]>(`/competitions/${cid}/editions`),
  editionChallenges: (eid: number) => http.get<CompetitionChallenge[]>(`/competitions/editions/${eid}/challenges`),
  challenge: (id: number) => http.get<CompetitionChallengeDetail>(`/competitions/challenges/${id}`),
  submitChallenge: (id: number, flag: string) =>
    http.post<{ success: boolean; message: string; points: number }>(
      `/competitions/challenges/${id}/submit`,
      { flag }
    ),
  createCompetition: (body: { name: string; description: string; icon: string }) =>
    http.post<Competition>('/admin/competitions', body),
  createEdition: (body: { competition_id: number; name: string; year: number }) =>
    http.post<CompetitionEdition>('/admin/competitions/editions', body),
  createChallenge: (body: { edition_id: number; title: string; category: string; difficulty: number; points: number; description: string; flag: string; attachment?: string | null }) =>
    http.post<CompetitionChallenge>('/admin/competitions/challenges', body),
  deleteCompetition: (cid: number, password: string) =>
    http.delete(`/admin/competitions/${cid}`, { password }),
  deleteEdition: (eid: number, password: string) =>
    http.delete(`/admin/competitions/editions/${eid}`, { password }),
  deleteChallenge: (cid: number) =>
    http.delete(`/admin/competitions/challenges/${cid}`),
  updateCompetition: (cid: number, body: { name: string; description: string; icon: string }) =>
    http.patch<Competition>(`/admin/competitions/${cid}`, body),
}
