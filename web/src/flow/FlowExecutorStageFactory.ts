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

const STANDARD = propVariants[0];

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

// The first type supports "import only."
type StageEntryMetadata = {
    tag: string | undefined;
    variant: PropVariant | undefined;
};

interface StageMappingInit {
    stage: FlowChallengeComponentName;
    variant: PropVariant;
    tag?: string;
}

const PVariant = P.when((x): x is PropVariant => propVariants.includes(x as PropVariant));

const PTag = P.when((x): x is string => typeof x === "string");

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
        StageEntries.map((entry) => [entry.stage, entry]),
    );

    public readonly stage: FlowChallengeComponentName;
    public readonly variant: PropVariant;
    public readonly tag: string;

    protected constructor({ stage, variant, tag }: DeepRequired<StageMappingInit>) {
        this.stage = stage;
        this.tag = tag;
        this.variant = variant;
    }

    /**
     * Create a `StageMapping` from a `StageEntry`.
     */
    public static async from(entry: StageEntry): Promise<StageMapping> {
        const { stage, fetch, variant, tag } = entry;
        const meta: StageEntryMetadata = { variant, tag };

        // prettier-ignore
        const init = match<StageEntryMetadata, StageMappingInit>(meta)
            .with({ tag: undefined, variant: undefined },
                () => ({ stage, variant: STANDARD }))
            .with({ variant: PVariant, tag: PTag },
                ({ tag, variant }) => ({ stage, variant, tag, }))
            .with({ variant: PVariant, tag: undefined },
                ({ variant }) => ({ stage, variant }))
            .with({ variant: undefined, tag: PTag },
                ({ tag }) => ({ stage, variant: STANDARD, tag }))
            .exhaustive();

        // A StageEntry supplies a tag only when the stage has been imported by default and so the
        // import event won't happen. Without it, the class constructor won't be available for tag
        // resolution anyway.
        const newtag = init.tag || (await fetch?.().then(resolveStageTag)) || stage;
        return new StageMapping({ ...init, tag: newtag });
    }
}
