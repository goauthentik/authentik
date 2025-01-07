/******************************************************************************
 * Copyright 2023 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { Connection, TextDocuments } from 'vscode-languageserver';
import type { DeepPartial, LangiumCoreServices, LangiumSharedCoreServices } from '../services.js';
import type { TextDocument } from '../workspace/documents.js';
import type { CallHierarchyProvider } from './call-hierarchy-provider.js';
import type { CodeActionProvider } from './code-action.js';
import type { CodeLensProvider } from './code-lens-provider.js';
import type { CompletionProvider } from './completion/completion-provider.js';
import type { DeclarationProvider } from './declaration-provider.js';
import type { DefinitionProvider } from './definition-provider.js';
import type { DocumentHighlightProvider } from './document-highlight-provider.js';
import type { DocumentLinkProvider } from './document-link-provider.js';
import type { DocumentSymbolProvider } from './document-symbol-provider.js';
import type { DocumentUpdateHandler } from './document-update-handler.js';
import type { ExecuteCommandHandler } from './execute-command-handler.js';
import type { FileOperationHandler } from './file-operation-handler.js';
import type { FoldingRangeProvider } from './folding-range-provider.js';
import type { Formatter } from './formatter.js';
import type { FuzzyMatcher } from './fuzzy-matcher.js';
import type { HoverProvider } from './hover-provider.js';
import type { ImplementationProvider } from './implementation-provider.js';
import type { InlayHintProvider } from './inlay-hint-provider.js';
import type { LanguageServer } from './language-server.js';
import type { NodeKindProvider } from './node-kind-provider.js';
import type { ReferencesProvider } from './references-provider.js';
import type { RenameProvider } from './rename-provider.js';
import type { SemanticTokenProvider } from './semantic-token-provider.js';
import type { SignatureHelpProvider } from './signature-help-provider.js';
import type { TypeHierarchyProvider } from './type-hierarchy-provider.js';
import type { TypeDefinitionProvider } from './type-provider.js';
import type { WorkspaceSymbolProvider } from './workspace-symbol-provider.js';
/**
 * Combined Core + LSP services of Langium (total services)
 */
export type LangiumServices = LangiumCoreServices & LangiumLSPServices;
/**
 * Combined Core + LSP shared services of Langium (total services)
 */
export type LangiumSharedServices = LangiumSharedCoreServices & LangiumSharedLSPServices;
/**
 * LSP services for a specific language of which Langium provides default implementations.
 */
export type LangiumLSPServices = {
    lsp: {
        CompletionProvider?: CompletionProvider;
        DocumentHighlightProvider?: DocumentHighlightProvider;
        DocumentSymbolProvider?: DocumentSymbolProvider;
        HoverProvider?: HoverProvider;
        FoldingRangeProvider?: FoldingRangeProvider;
        DefinitionProvider?: DefinitionProvider;
        TypeProvider?: TypeDefinitionProvider;
        ImplementationProvider?: ImplementationProvider;
        ReferencesProvider?: ReferencesProvider;
        CodeActionProvider?: CodeActionProvider;
        SemanticTokenProvider?: SemanticTokenProvider;
        RenameProvider?: RenameProvider;
        Formatter?: Formatter;
        SignatureHelp?: SignatureHelpProvider;
        CallHierarchyProvider?: CallHierarchyProvider;
        TypeHierarchyProvider?: TypeHierarchyProvider;
        DeclarationProvider?: DeclarationProvider;
        InlayHintProvider?: InlayHintProvider;
        CodeLensProvider?: CodeLensProvider;
        DocumentLinkProvider?: DocumentLinkProvider;
    };
    shared: LangiumSharedServices;
};
/**
 * LSP services shared between multiple languages of which Langium provides default implementations.
 */
export type LangiumSharedLSPServices = {
    lsp: {
        Connection?: Connection;
        DocumentUpdateHandler: DocumentUpdateHandler;
        ExecuteCommandHandler?: ExecuteCommandHandler;
        FileOperationHandler?: FileOperationHandler;
        FuzzyMatcher: FuzzyMatcher;
        LanguageServer: LanguageServer;
        NodeKindProvider: NodeKindProvider;
        WorkspaceSymbolProvider?: WorkspaceSymbolProvider;
    };
    workspace: {
        TextDocuments: TextDocuments<TextDocument>;
    };
};
/**
 * Language-specific LSP services to be partially overridden via dependency injection.
 */
export type PartialLangiumLSPServices = DeepPartial<LangiumLSPServices>;
/**
 * Language-specific services to be partially overridden via dependency injection.
 */
export type PartialLangiumServices = DeepPartial<LangiumServices>;
/**
 * Shared LSP services to be partially overridden via dependency injection.
 */
export type PartialLangiumSharedLSPServices = DeepPartial<LangiumSharedLSPServices>;
/**
 * Shared services to be partially overridden via dependency injection.
 */
export type PartialLangiumSharedServices = DeepPartial<LangiumSharedServices>;
//# sourceMappingURL=lsp-services.d.ts.map