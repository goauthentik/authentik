/**
 * @file Types for the Monaco modules that ship without declarations.
 */

declare module "monaco-editor/editor/contrib/suggest/browser/suggestController" {}

declare module "monaco-editor/languages/features/common/lspLanguageFeatures" {
    import type { IDisposable, languages, Uri } from "monaco-editor/editor/editor.api";

    /**
     * Resolves the language service that answers for the given models.
     */
    export type WorkerAccessor<T> = (...uris: Uri[]) => Promise<T>;

    export class CompletionAdapter<T> implements languages.CompletionItemProvider {
        constructor(worker: WorkerAccessor<T>, triggerCharacters: string[]);
        triggerCharacters: string[];
        provideCompletionItems: languages.CompletionItemProvider["provideCompletionItems"];
    }

    export class HoverAdapter<T> implements languages.HoverProvider {
        constructor(worker: WorkerAccessor<T>);
        provideHover: languages.HoverProvider["provideHover"];
    }

    export class FoldingRangeAdapter<T> implements languages.FoldingRangeProvider {
        constructor(worker: WorkerAccessor<T>);
        provideFoldingRanges: languages.FoldingRangeProvider["provideFoldingRanges"];
    }

    export class DiagnosticsAdapter<T> implements IDisposable {
        constructor(
            languageId: string,
            worker: WorkerAccessor<T>,
            configChangeEvent: (listener: () => void) => IDisposable,
        );
        dispose(): void;
    }
}

declare module "monaco-editor/languages/features/css/cssWorker" {
    /**
     * The model data a language service reads, as Monaco's worker mirrors it.
     */
    export interface MirrorModel {
        readonly uri: { toString(): string };
        readonly version: number;
        getValue(): string;
    }

    export interface CSSWorkerContext {
        getMirrorModels(): MirrorModel[];
    }

    export interface CSSWorkerCreateData {
        languageId: "css" | "less" | "scss";
        options: {
            validate?: boolean;
            lint?: Record<string, "ignore" | "warning" | "error">;
            data?: { useDefaultDataProvider?: boolean };
        };
    }

    export class CSSWorker {
        constructor(ctx: CSSWorkerContext, createData: CSSWorkerCreateData);
    }
}
