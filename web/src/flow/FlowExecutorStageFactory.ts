import "#flow/sources/apple/AppleLoginInit";
import "#flow/sources/plex/PlexLoginInit";
import "#flow/sources/telegram/TelegramLogin";
import "#flow/stages/FlowErrorStage";
import "#flow/stages/FlowFrameStage";
import "#flow/stages/RedirectStage";

import StageModules from "#flow/FlowExecutorStages";
import type { FlowChallengeComponentName, StageModuleCallback } from "#flow/types";

import { match, P } from "ts-pattern";

export type { FlowChallengeComponentName, StageModuleCallback };
export const propVariants = ["standard", "challenge", "inspect"] as const;
export type PropVariant = (typeof propVariants)[number];

// We have several patterns for the client-side components that handle a stage. In most cases, the
// stage component-name and the client-side element-name are the same, but not always. Most stages
// need CSS-related help to be visually attractive, but "challenge" stages do not. Most stages can
// be imported as-needed, but some must be pre-loaded.

// StageMapping describes the metadata needed to load and invoke a stage.  If a tag name is not
// supplied it automatically tries to derive its tag name by first seeing if there's an import
// function supplied; if it is, it imports the web component and derives the tag name from the
// tag registered with the browser; if not, it uses the token name by default.  If the tag name
// needs to import the component before deriving the name, it does that automatically.

class StageMapping {
    // Singleton pattern to reduce calls to `import`
    static tokenCache = new Map<FlowChallengeComponentName, StageMapping>();

    public token!: FlowChallengeComponentName;
    public variant!: PropVariant;
    #tag?: string;
    #importCallback?: StageModuleCallback;

    constructor(token: FlowChallengeComponentName, variant: PropVariant, tag?: string, callback?: StageModuleCallback) {
        const instance = StageMapping.tokenCache.get(token);
        if (instance) {
            return instance;
        }

        this.token = token;
        this.#tag = tag;
        this.variant = variant;
        this.#importCallback = callback;
        StageMapping.tokenCache.set(token, this);
    }

    // Warning: this is secretly an async operation and returns a Promise. The internal async IIFE
    // is a workaround for Typescript's "accessors cannot use await."
    /* async */ get tag() {
        return (async () => {
            if (this.#tag) {
                return Promise.resolve(this.#tag);
            }

            if (!this.#importCallback) {
                return Promise.resolve(this.token);
            }

            const module = await this.#importCallback();
            const StageConstructor = module.default;
            const tag = window.customElements.getName(StageConstructor);
            if (!tag) {
                const error = `Failed to load module: no client stage found for component ${this.token}`;
                // eslint-disable-next-line no-console
                console.trace(error);
                throw new TypeError(error);
            }
            this.#tag = tag;
            return Promise.resolve(tag);
        })();
    }
}

// The first type supports "import only."
type StageEntryMetadata = [] | [tag: string] | [variant: PropVariant] | [tag: string, variant: PropVariant];

const STANDARD = propVariants[0];
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isImport = (x: any): x is StageModuleCallback => typeof x === "function";
const PVariant = P.when((x): x is PropVariant => typeof x === "string" && propVariants.includes(x as PropVariant));
const PTag = P.when((x): x is string => typeof x === "string" && x.includes("-"));

/**
 * A mapping of server-side stage tokens to client-side custom element tags, along with the variant
 * of props they consume and an optional import callback for lazy-loading.
 *
 * @remarks
 * This is the actual table of stages consumed by the FlowExecutor.
 * It is generated from the more concise `StageModuleRecord` above, which is easier to read and maintain.
 * The `StageModuleRecord` allows for specifying just the serverComponent, or the serverComponent and variant,
 * or the serverComponent and tag, or all three, and it can also include an import callback if the stage should be lazy-loaded.
 * The code below normalizes all of these possibilities into a consistent format that the FlowExecutor can use.
 */
export const StageMappings: ReadonlyMap<FlowChallengeComponentName, StageMapping> = new Map(
    StageModules.map((stageEntry) => {
        const [serverComponent, ...entry] = stageEntry;
        const last = entry.at(-1);
        const importfn = isImport(last) ? last : undefined;
        const meta = (importfn ? entry.slice(0, -1) : entry) as StageEntryMetadata;

        // prettier-ignore
        return [
            serverComponent,
            match<StageEntryMetadata, StageMapping>(meta)
                .with([], () => new StageMapping(serverComponent, STANDARD, undefined, importfn))
                .with([PTag, PVariant], ([tag, variant]) => new StageMapping(serverComponent, variant, tag, importfn))
                .with([PVariant], ([variant]) => new StageMapping(serverComponent, variant, undefined, importfn))
                .with([PTag], ([tag]) => new StageMapping(serverComponent, STANDARD, tag, importfn))
                .exhaustive(),
        ];
    })
);
