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
 * The lexicon database encrypted with `seal`, committed so CI can audit without the plaintext.
 */
export const SEALED_DATABASE_PATH = join(PACKAGE_ROOT, `${DATABASE_NAME}.gpg`);

/**
 * Environment variable holding the passphrase for {@linkcode SEALED_DATABASE_PATH}.
 */
export const PASSPHRASE_ENV = "LEXICON_AUDIT_PASSPHRASE";

/**
 * Lexicon words reviewed as false positives. Ignored by git; `build` stores it in the database.
 */
export const ALLOWLIST_PATH = join(PACKAGE_ROOT, "allowlist.tsv");

/**
 * Bumped whenever the schema or normalization rules change.
 */
export const SCHEMA_VERSION = 2;

/**
 * Default minimum length of a lexicon entry, in characters, outside CJK locales. Shorter entries
 * are mostly abbreviations and letter pairs that collide with codes and identifiers.
 */
export const DEFAULT_MIN_LENGTH = 3;

export const TIERS = ["vulgar", "offensive", "sensitive"] as const;

export type Tier = (typeof TIERS)[number];

export function isTier(value: string): value is Tier {
    return (TIERS as readonly string[]).includes(value);
}
