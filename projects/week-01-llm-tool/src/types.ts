export type MessageRole = 'system' | 'user' | 'assistant';

export interface Message {
  role: MessageRole;
  content: string;
  timestamp?: number;
}

export interface LLMRequest {
  model: string;
  messages: Message[];
  temperature?: number;
  max_tokens?: number;
}

export interface LLMResponse {
  content: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
  };
}

export type LLMError =
  | { type: 'network'; message: string }
  | { type: 'timeout'; ms: number }
  | { type: 'api'; code: number; message: string };
