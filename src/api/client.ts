declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData: string
        initDataUnsafe: { user?: { id: number; username?: string; first_name?: string } }
        ready: () => void
        expand: () => void
        close: () => void
        themeParams: Record<string, string>
      }
    }
  }
}

const BASE_URL = '/api'

function getInitData(): string {
  return window.Telegram?.WebApp?.initData || ''
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'X-Telegram-Init-Data': getInitData() },
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': getInitData(),
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': getInitData(),
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'DELETE',
    headers: { 'X-Telegram-Init-Data': getInitData() },
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'X-Telegram-Init-Data': getInitData() },
    body: formData,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function getTelegramUser() {
  return window.Telegram?.WebApp?.initDataUnsafe?.user
}
