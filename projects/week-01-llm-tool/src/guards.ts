import { LLMError } from './types.js';

export function isNetworkError(err: LLMError): boolean {
  return err.type === 'network';
}

export function isTimeoutError(err: LLMError): boolean {
  return err.type === 'timeout';
}

export function isApiError(err: LLMError): boolean {
  return err.type === 'api';
}
