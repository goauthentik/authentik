/******************************************************************************
 * Copyright 2023 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import { CompletionItemKind, SymbolKind } from 'vscode-languageserver';
export class DefaultNodeKindProvider {
    getSymbolKind() {
        return SymbolKind.Field;
    }
    getCompletionItemKind() {
        return CompletionItemKind.Reference;
    }
}
//# sourceMappingURL=node-kind-provider.js.map