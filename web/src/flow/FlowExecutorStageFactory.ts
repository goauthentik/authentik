/**
 * We have several patterns for the client-side components that handle a stage. In most cases, the
 * stage component-name and the client-side element-name are the same, but not always. Most stages
 * need CSS-related help to be visually attractive, but "challenge" stages do not. Most stages can
 * be imported as-needed, but some must be pre-loaded.
 */

import "#flow/sources/apple/AppleLoginInit";
import "#flow/sources/plex/PlexLoginInit";
import "#flow/sources/telegram/TelegramLogin";
import "#flow/stages/FlowErrorStage";
import "#flow/stages/FlowFrameStage";
import "#flow/stages/RedirectStage";

import StageModules, { StageEntry } from "#flow/FlowExecutorStages";
import type { FlowChallengeComponentName, StageModuleCallback } from "#flow/types";

import { match, P } from "ts-pattern";

export type { FlowChallengeComponentName, StageModuleCallback };
export const propVariants = ["standard", "challenge"] as const;
export type PropVariant = (typeof propVariants)[number];

// The first type supports "import only."
type StageEntryMetadata =
    | []
    | [tag: string]
    | [variant: PropVariant]
    | [tag: string, variant: PropVariant];

const STANDARD = propVariants[0];
const isImport = (x: unknown): x is StageModuleCallback => typeof x === "function";
const PVariant = P.when(
    (x): x is PropVariant => typeof x === "string" && propVariants.includes(x as PropVariant),
);
const PTag = P.when((x): x is string => typeof x === "string" && x.includes("-"));

interface StageMappingInit {
    token: FlowChallengeComponentName;
    variant: PropVariant;
    tag?: string | null;
    callback?: StageModuleCallback | null;
}

/**
 * StageMapping describes the metadata needed to load and invoke a stage.
 * If a tag name is not supplied it automatically tries to derive its tag name by first seeing if there's an import
 * function supplied; if it is, it imports the web component and derives the tag name from the
 * tag registered with the browser; if not, it uses the token name by default.  If the tag name
 * needs to import the component before deriving the name, it does that automatically.
 */
class StageMapping {
    public token: FlowChallengeComponentName;
    public variant: PropVariant;

    #tag: string | null = null;
    #importCallback: StageModuleCallback | null = null;

    constructor({ token, variant, tag = null, callback = null }: StageMappingInit) {
        this.token = token;
        this.#tag = tag;
        this.variant = variant;
        this.#importCallback = callback;
    }

    get tag(): Promise<string> {
        if (this.#tag) {
            return Promise.resolve(this.#tag);
        }

        if (!this.#importCallback) {
            return Promise.resolve(this.token);
        }

        return this.#importCallback()
            .then((module) => {
                const StageConstructor = module.default;
                const tag = window.customElements.getName(StageConstructor);

                if (!tag) {
                    const error = new TypeError(
                        `Failed to load module: no client stage found for component ${this.token}`,
                    );

                    // eslint-disable-next-line no-console
                    console.trace(error);
                    throw error;
                }

                this.#tag = tag;

                return Promise.resolve(tag);
            })
            .catch((cause) => {
                throw new TypeError(`Failed to load module for component ${this.token}`, { cause });
            });
    }

    /**
     * Create a `StageMapping` from a `StageEntry`.
     */
    public static from(entry: StageEntry): StageMapping {
        const [token, ...rest] = entry;

        const last = rest.at(-1);
        const callback = isImport(last) ? last : null;
        const meta = (callback ? rest.slice(0, -1) : rest) as StageEntryMetadata;

        const init = match<StageEntryMetadata, StageMappingInit>(meta)
            .with([], () => ({ token, variant: STANDARD, callback }))
            .with([PTag, PVariant], ([tag, variant]) => ({ token, variant, tag, callback }))
            .with([PVariant], ([variant]) => ({ token, variant, callback }))
            .with([PTag], ([tag]) => ({ token, variant: STANDARD, tag, callback }))
            .exhaustive();

        return new StageMapping(init);
    }
}

/**
 * A mapping of server-side stage tokens to client-side custom element tags, along with the variant
 * of props they consume and an optional import callback for lazy-loading.
 *
 * @remarks
 * This is the actual table of stages consumed by the FlowExecutor. It is generated from the more
 * concise `StageModules` table in the file `FlowExecutorStages`, which is easier to read and
 * maintain. The `StageEntry` allows for specifying just the serverComponent, or the
 * serverComponent and variant, or the serverComponent and tag, or all three, and it can also
 * include an import callback if the stage should be lazy-loaded. The code below normalizes all of
 * these possibilities into a consistent format that the FlowExecutor can use.
 */
export const StageMappings: ReadonlyMap<FlowChallengeComponentName, () => StageMapping> = new Map(
    StageModules.map((stageEntry) => {
        const [token] = stageEntry;
        return [token, () => StageMapping.from(stageEntry)] as const;
    }),
);
