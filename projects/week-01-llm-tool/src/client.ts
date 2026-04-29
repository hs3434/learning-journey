import { request } from './request.js';
import type { LLMRequest, LLMResponse, LLMError } from './types.js';

export async function callLLM(req: LLMRequest): Promise<{ success: true; data: LLMResponse } | { success: false; error: LLMError }> {
  const baseUrl = process.env.LLM_BASE_URL || 'https://api.openai.com/v1';
  const apiKey = process.env.LLM_API_KEY || '';

  const result = await request<LLMResponse>(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify(req),
  });

  return result as { success: true; data: LLMResponse } | { success: false; error: LLMError };
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  retries: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === retries - 1) throw err;
      await new Promise(res => setTimeout(res, delay * (i + 1)));
    }
  }
  throw new Error('unreachable');
}

export async function batchCallLLM(
  requests: LLMRequest[]
): Promise<Array<{ success: true; data: LLMResponse } | { success: false; error: LLMError }>> {
  const promises = requests.map(req => callLLM(req));
  const results = await Promise.allSettled(promises);

  return results.map((r) => {
    if (r.status === 'fulfilled') return r.value;
    return { success: false, error: { type: 'network', message: String(r.reason) } as LLMError };
  });
}
