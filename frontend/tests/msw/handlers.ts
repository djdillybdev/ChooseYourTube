import { http, passthrough } from 'msw';

export const handlers = [http.all('*', async () => passthrough())];
