export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export async function fetchPaginated<T>(
  url: string,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<T>> {
  const res = await fetch(`${url}?page=${page}&pageSize=${pageSize}`);
  return res.json() as Promise<PaginatedResponse<T>>;
}
