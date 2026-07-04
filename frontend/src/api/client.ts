import type { AnalyzeResponse, ListReportEntry, MotorProfile, ReportDetail, UploadResponse } from '../types'

const BASE = '/api/v1'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  async uploadDataset(file: File): Promise<UploadResponse> {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
    return handleResponse<UploadResponse>(res)
  },

  async analyzeReport(reportId: string, motorProfile?: MotorProfile | null): Promise<AnalyzeResponse> {
    const hasProfile = motorProfile && Object.values(motorProfile).some(v => v !== undefined && v !== '' && v !== null)
    const res = await fetch(`${BASE}/analyze/${reportId}`, {
      method:  'POST',
      headers: hasProfile ? { 'Content-Type': 'application/json' } : {},
      body:    hasProfile ? JSON.stringify({ motor_profile: motorProfile }) : undefined,
    })
    return handleResponse<AnalyzeResponse>(res)
  },

  async listReports(limit = 50): Promise<ListReportEntry[]> {
    const res = await fetch(`${BASE}/reports?limit=${limit}`)
    const data = await handleResponse<{ reports: ListReportEntry[] }>(res)
    return data.reports
  },

  async getReport(reportId: string): Promise<ReportDetail> {
    const res = await fetch(`${BASE}/reports/${reportId}`)
    return handleResponse<ReportDetail>(res)
  },

  async deleteReport(reportId: string): Promise<void> {
    const res = await fetch(`${BASE}/reports/${reportId}`, { method: 'DELETE' })
    if (!res.ok && res.status !== 204) {
      const body = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(body.detail ?? `HTTP ${res.status}`)
    }
  },

  exportUrl(type: 'pdf' | 'csv' | 'xlsx' | 'json', reportId: string): string {
    return `${BASE}/export/${type}/${reportId}`
  },
}
