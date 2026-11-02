/**
 * @file The contract between the editor and the language services it loads.
 */

import type { Disposable } from "#elements/CodeEditor/languages/schemas";
import type { CodeEditorSchema } from "#elements/CodeEditor/shared";

export interface LanguageService {
    /**
     * Validates, completes and describes the model's content with the schema, until disposed.
     */
    associateSchema?(modelURI: string, schema: CodeEditorSchema): Disposable;
}
