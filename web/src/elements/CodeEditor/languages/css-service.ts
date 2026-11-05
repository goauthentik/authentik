/**
 * @remarks
 *   Runs Monaco's CSS language service on the page instead of in a web worker. Its `register`
 *   entry point would start a worker and, through Monaco's worker setup, load every editor
 *   feature this package leaves out.
 * @file CSS suggestions, hovers and validation.
 */

import { PageWorkerContext } from "#elements/CodeEditor/languages/page-worker";

import { languages } from "monaco-editor/editor/editor.api";
import {
    CompletionAdapter,
    DiagnosticsAdapter,
    FoldingRangeAdapter,
    HoverAdapter,
} from "monaco-editor/languages/features/common/lspLanguageFeatures";
import { CSSWorker } from "monaco-editor/languages/features/css/cssWorker";

const service = new CSSWorker(PageWorkerContext, {
    languageId: "css",
    options: {
        validate: true,
        data: { useDefaultDataProvider: true },
    },
});

const worker = () => Promise.resolve(service);

languages.registerCompletionItemProvider("css", new CompletionAdapter(worker, ["/", "-", ":"]));
languages.registerHoverProvider("css", new HoverAdapter(worker));
languages.registerFoldingRangeProvider("css", new FoldingRangeAdapter(worker));

new DiagnosticsAdapter("css", worker, (listener) => {
    // The adapter only checks models created after it, so check the existing ones once.
    queueMicrotask(listener);

    return { dispose() {} };
});
