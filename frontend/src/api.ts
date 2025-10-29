import { Channel, Video, ApiErrorResponse } from "./types";

const DEFAULT_API_PORT = "8009";

const getBaseUrl = () => {
  const envUrl =
    typeof import.meta !== "undefined" ? import.meta.env?.VITE_API_BASE_URL : undefined;
  if (envUrl) {
    return envUrl;
  }

  if (typeof window !== "undefined" && window.location) {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:${DEFAULT_API_PORT}`;
  }

  return `http://localhost:${DEFAULT_API_PORT}`;
};

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;

    try {
      const errorBody = (await response.json()) as ApiErrorResponse;
      if (typeof errorBody.detail === "string") {
        errorMessage = errorBody.detail;
      } else if (Array.isArray(errorBody.detail) && errorBody.detail.length > 0) {
        const messages = errorBody.detail
          .map((item) => item?.msg)
          .filter(Boolean)
          .join("\n");
        if (messages) {
          errorMessage = messages;
        }
      }
    } catch (error) {
      // ignore JSON parsing errors and use default error message
    }

    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}

export async function fetchChannels(signal?: AbortSignal): Promise<Channel[]> {
  const response = await fetch(`${getBaseUrl()}/channels/`, { signal });
  return handleResponse<Channel[]>(response);
}

export async function createChannel(handle: string): Promise<Channel> {
  const response = await fetch(`${getBaseUrl()}/channels/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ handle }),
  });

  return handleResponse<Channel>(response);
}

export async function fetchVideosForChannel(
  channelId: string,
  signal?: AbortSignal
): Promise<Video[]> {
  const response = await fetch(`${getBaseUrl()}/videos/by-channel/${channelId}`, {
    signal,
  });
  return handleResponse<Video[]>(response);
}
