/**
 * @file Lets Monaco's language services, written to run in a web worker, run on the page.
 */

import { editor } from "monaco-editor/editor/editor.api";
import type { CSSWorkerContext } from "monaco-editor/languages/features/css/cssWorker";

/**
 * Gives a language service the editor's models, in place of the copies a worker would hold.
 */
export const PageWorkerContext: CSSWorkerContext = {
    getMirrorModels: () =>
        editor.getModels().map((model) => ({
            uri: model.uri,
            version: model.getVersionId(),
            getValue: () => model.getValue(),
        })),
};
