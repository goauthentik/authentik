export type Spread = { [key: string]: unknown };

/**
 * For builder functions, valid data attributes that can be placed on custom components.
 */

export type DataRecord = {
    [key: `data-${string}`]: string | boolean;
};

/**
 * For builder functions, aria attributes that can be placed on custom components.
 */

export type AriaRecord = {
    [key: `aria-${string}`]: string;
};

/**
 * This may be overkill.
 */

type _ElementRestBase = DataRecord & AriaRecord;

export interface ElementRest extends _ElementRestBase {
    id?: string;
    class?: string;
    style?: string;
    slot?: string;
    title?: string;
    part?: string;
}
