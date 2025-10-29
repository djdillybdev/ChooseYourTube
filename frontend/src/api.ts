import { Channel, Video } from './types'

const DEFAULT_BASE_URL = 'http://localhost:8009'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || DEFAULT_BASE_URL

async function fetchJSON<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init)

  if (!response.ok) {
    let message = response.statusText
    try {
      const data = await response.json()
      message = data.detail || data.message || message
    } catch (error) {
      // ignore json parse errors and fall back to status text
    }

    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export async function getChannels(): Promise<Channel[]> {
  return fetchJSON<Channel[]>(`${API_BASE_URL}/channels`)
}

export async function addChannel(handle: string): Promise<Channel> {
  return fetchJSON<Channel>(`${API_BASE_URL}/channels`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ handle }),
  })
}

export async function getVideosForChannel(channelId: string): Promise<Video[]> {
  return fetchJSON<Video[]>(`${API_BASE_URL}/videos/by-channel/${channelId}`)
}

export function getApiBaseUrl() {
  return API_BASE_URL
}
