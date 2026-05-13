export type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

export async function request<T, E = Error>(
  url: string,
  options?: RequestInit
): Promise<Result<T, E>> {
  try {
    const res = await fetch(url, options);
    const data = await res.json() as T;
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error as E };
  }
}
