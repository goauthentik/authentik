import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

export const PACKAGE_ROOT = resolve(__dirname, "..");

export const DATABASE_NAME = "lexicon-audit.db";

export const OUT_DIR = join(PACKAGE_ROOT, "out");

export const DATABASE_PATH = join(OUT_DIR, DATABASE_NAME);

/**
 * Default location of the private lexicon dump. Ignored by git.
 */
export const CORPUS_DIR = join(PACKAGE_ROOT, "corpus", "words");

/**
 * Lexicon words reviewed as false positives. Ignored by git; `build` stores it in the database.
 */
export const ALLOWLIST_PATH = join(PACKAGE_ROOT, "allowlist.tsv");

/**
 * Bumped whenever the schema or normalization rules change.
 */
export const SCHEMA_VERSION = 2;

export const TIERS = ["vulgar", "offensive", "sensitive"] as const;

export type Tier = (typeof TIERS)[number];

export function isTier(value: string): value is Tier {
    return (TIERS as readonly string[]).includes(value);
}
