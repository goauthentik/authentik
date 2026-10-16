const seed = 1;

export interface Wrapped {
    seed: number;
}

export type Alias = Wrapped;
export const wrapped: Wrapped = { seed };
