export interface UserConfig {
  apiKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
  timeout: number;
  retries: number;
}

export type PartialConfig = Partial<UserConfig>;
export type RequiredConfig = Required<PartialConfig>;
export type PublicConfig = Omit<UserConfig, 'apiKey'>;
export type ReadonlyConfig = Readonly<UserConfig>;

type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type { DeepPartial };
