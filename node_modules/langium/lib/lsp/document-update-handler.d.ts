/******************************************************************************
 * Copyright 2023 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import { type DidChangeWatchedFilesParams, type TextDocumentChangeEvent } from 'vscode-languageserver';
import { URI } from '../utils/uri-utils.js';
import type { DocumentBuilder } from '../workspace/document-builder.js';
import type { TextDocument } from '../workspace/documents.js';
import type { WorkspaceLock } from '../workspace/workspace-lock.js';
import type { LangiumSharedServices } from './lsp-services.js';
import type { WorkspaceManager } from '../workspace/workspace-manager.js';
/**
 * Shared service for handling text document changes and watching relevant files.
 */
export interface DocumentUpdateHandler {
    /**
     * A content change event was triggered by the `TextDocuments` service.
     */
    didChangeContent(change: TextDocumentChangeEvent<TextDocument>): void;
    /**
     * The client detected changes to files and folders watched by the language client.
     */
    didChangeWatchedFiles(params: DidChangeWatchedFilesParams): void;
}
export declare class DefaultDocumentUpdateHandler implements DocumentUpdateHandler {
    protected readonly workspaceManager: WorkspaceManager;
    protected readonly documentBuilder: DocumentBuilder;
    protected readonly workspaceLock: WorkspaceLock;
    constructor(services: LangiumSharedServices);
    protected registerFileWatcher(services: LangiumSharedServices): void;
    protected fireDocumentUpdate(changed: URI[], deleted: URI[]): void;
    didChangeContent(change: TextDocumentChangeEvent<TextDocument>): void;
    didChangeWatchedFiles(params: DidChangeWatchedFilesParams): void;
}
//# sourceMappingURL=document-update-handler.d.ts.map