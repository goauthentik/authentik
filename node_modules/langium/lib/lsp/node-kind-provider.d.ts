/******************************************************************************
 * Copyright 2023 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { AstNode, AstNodeDescription } from '../syntax-tree.js';
import { CompletionItemKind, SymbolKind } from 'vscode-languageserver';
/**
 * This service consolidates the logic for gathering LSP kind information based on AST nodes or their descriptions.
 */
export interface NodeKindProvider {
    /**
     * Returns a `SymbolKind` as used by `WorkspaceSymbolProvider` or `DocumentSymbolProvider`.
     */
    getSymbolKind(node: AstNode | AstNodeDescription): SymbolKind;
    /**
     * Returns a `CompletionItemKind` as used by the `CompletionProvider`.
     */
    getCompletionItemKind(node: AstNode | AstNodeDescription): CompletionItemKind;
}
export declare class DefaultNodeKindProvider implements NodeKindProvider {
    getSymbolKind(): SymbolKind;
    getCompletionItemKind(): CompletionItemKind;
}
//# sourceMappingURL=node-kind-provider.d.ts.map