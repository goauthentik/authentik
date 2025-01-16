/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { Position, Range, RenameParams, TextDocumentPositionParams, WorkspaceEdit } from 'vscode-languageserver-protocol';
import type { CancellationToken } from '../utils/cancellation.js';
import type { GrammarConfig } from '../languages/grammar-config.js';
import type { NameProvider } from '../references/name-provider.js';
import type { References } from '../references/references.js';
import type { LangiumServices } from './lsp-services.js';
import type { CstNode } from '../syntax-tree.js';
import type { MaybePromise } from '../utils/promise-utils.js';
import type { LangiumDocument } from '../workspace/documents.js';
/**
 * Language-specific service for handling rename requests and prepare rename requests.
 */
export interface RenameProvider {
    /**
     * Handle a rename request.
     *
     * @throws `OperationCancelled` if cancellation is detected during execution
     * @throws `ResponseError` if an error is detected that should be sent as response to the client
     */
    rename(document: LangiumDocument, params: RenameParams, cancelToken?: CancellationToken): MaybePromise<WorkspaceEdit | undefined>;
    /**
     * Handle a prepare rename request.
     *
     * @throws `OperationCancelled` if cancellation is detected during execution
     * @throws `ResponseError` if an error is detected that should be sent as response to the client
     */
    prepareRename(document: LangiumDocument, params: TextDocumentPositionParams, cancelToken?: CancellationToken): MaybePromise<Range | undefined>;
}
export declare class DefaultRenameProvider implements RenameProvider {
    protected readonly references: References;
    protected readonly nameProvider: NameProvider;
    protected readonly grammarConfig: GrammarConfig;
    constructor(services: LangiumServices);
    rename(document: LangiumDocument, params: RenameParams): Promise<WorkspaceEdit | undefined>;
    prepareRename(document: LangiumDocument, params: TextDocumentPositionParams): MaybePromise<Range | undefined>;
    protected renameNodeRange(doc: LangiumDocument, position: Position): Range | undefined;
    protected isNameNode(leafNode: CstNode | undefined): boolean | undefined;
}
//# sourceMappingURL=rename-provider.d.ts.map