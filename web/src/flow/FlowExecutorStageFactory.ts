/**
 * We have several patterns for the client-side components that handle a stage. In most cases, the
 * stage component-name and the client-side element-name are the same, but not always. Most stages
 * need CSS-related help to be visually attractive, but "challenge" stages do not. Most stages can
 * be imported as-needed, but some must be pre-loaded.
 */

import { ResolvedDefaultESModule } from "#common/modules/types";
import { DeepRequired } from "#common/types";

import { StageEntries, StageEntry } from "#flow/FlowExecutorStages";
import type {
    BaseStageConstructor,
    FlowChallengeComponentName,
    StageModuleCallback,
} from "#flow/types";

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

export class StageMappingError extends TypeError {
    constructor(message: string, options?: ErrorOptions) {
        super(message, options);
        this.name = "StageMappingError";
    }
}

/**
 * Resolve a stage constructor to its custom element tag name.
 */
function resolveStageTag(module: ResolvedDefaultESModule<BaseStageConstructor>): string {
    const StageConstructor = module.default;
    const tag = window.customElements.getName(StageConstructor);

    if (!tag) {
        const error = new StageMappingError(
            `Failed to load module: No client stage found for component`,
        );

        throw error;
    }

    return tag;
}

interface StageMappingInit {
    token: FlowChallengeComponentName;
    variant: PropVariant;
    tag?: string;
}

/**
 * The metadata needed to load and invoke a stage.
 */
export class StageMapping {
    /**
     * A mapping of server-side stage tokens to client-side custom element tags.
     *
     * This can be used to determine if a given stage component has a corresponding client-side stage.
     */
    public static readonly registry: ReadonlyMap<FlowChallengeComponentName, StageEntry> = new Map(
        StageEntries.map((entry) => [entry[0], entry]),
    );

    public readonly token: FlowChallengeComponentName;
    public readonly variant: PropVariant;
    public readonly tag: string;

    protected constructor({ token, variant, tag }: DeepRequired<StageMappingInit>) {
        this.token = token;
        this.tag = tag;
        this.variant = variant;
    }

    /**
     * Create a `StageMapping` from a `StageEntry`.
     */
    public static async from([token, ...rest]: StageEntry): Promise<StageMapping> {
        const last = rest.at(-1);
        const callback = isImport(last) ? last : null;
        const meta = (callback ? rest.slice(0, -1) : rest) as StageEntryMetadata;

        const init = match<StageEntryMetadata, StageMappingInit>(meta)
            .with([], () => ({ token, variant: STANDARD }))
            .with([PTag, PVariant], ([tag, variant]) => ({ token, variant, tag }))
            .with([PVariant], ([variant]) => ({ token, variant }))
            .with([PTag], ([tag]) => ({ token, variant: STANDARD, tag }))
            .exhaustive();

        const tag = init.tag || (await callback?.().then(resolveStageTag));

        if (!tag) {
            throw new StageMappingError(
                `Invalid stage entry for component ${token}: No tag or import callback provided.`,
            );
        }

        return new StageMapping({ ...init, tag });
    }
}
