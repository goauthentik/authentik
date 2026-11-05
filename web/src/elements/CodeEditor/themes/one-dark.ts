/**
 * @file One Dark theme for Monaco.
 * @see https://github.com/azemoh/vscode-onedark (MIT, vendored at 37abe2b, see one-dark.LICENSE)
 */

import type { editor } from "monaco-editor/editor/editor.api";

interface TokenColor {
    scope?: string | string[];
    settings: { foreground?: string; background?: string; fontStyle?: string };
}

/**
 * Monaco's language definitions emit Monarch token names rather than TextMate scopes.
 * Each maps to the TextMate scope whose color it takes.
 */
const MonarchScopes: Record<string, string> = {
    "number": "constant.numeric",
    "tag": "entity.name.tag",
    "metatag": "entity.name.tag",
    "attribute.name": "entity.other.attribute-name",
    "attribute.value": "string",
    "type": "entity.name.type",
    "namespace": "entity.name.module",
    "operators": "keyword.operator",
    "regexp": "string.embedded",
    // Monaco's JSON tokenizer.
    "string.key.json": "support.dictionary.json",
    "keyword.json": "constant.language",
};

function toRule(token: string, { foreground, background, fontStyle }: TokenColor["settings"]) {
    return {
        token,
        foreground: foreground?.replace("#", ""),
        background: background?.replace("#", ""),
        fontStyle,
    } satisfies editor.ITokenThemeRule;
}

function createRules(tokenColors: TokenColor[]): editor.ITokenThemeRule[] {
    const settingsByScope = new Map<string, TokenColor["settings"]>();

    for (const { scope, settings } of tokenColors) {
        for (const name of [scope ?? []].flat()) {
            // Scope selectors with exclusions have no Monaco equivalent.
            if (!name.includes(" ")) settingsByScope.set(name, settings);
        }
    }

    const rules = Array.from(settingsByScope, ([token, settings]) => toRule(token, settings));

    for (const [token, scope] of Object.entries(MonarchScopes)) {
        const settings = settingsByScope.get(scope);

        if (settings) rules.push(toRule(token, settings));
    }

    return rules;
}

//#region Vendored theme

const OneDarkTheme = {
    tokenColors: [
        {
            settings: {
                background: "#282c34",
                foreground: "#abb2bf",
                findHighlight: "#FFE792",
                findHighlightForeground: "#000000",
                selectionBorder: "#222218",
                activeGuide: "#9D550FB0",
                bracketsForeground: "#F8F8F2A5",
                bracketsOptions: "underline",
                bracketContentsForeground: "#F8F8F2A5",
                bracketContentsOptions: "underline",
                tagsOptions: "stippled_underline",
            },
        },
        {
            name: "Comment",
            scope: "comment",
            settings: {
                foreground: "#5c6370",
                fontStyle: "italic",
            },
        },
        {
            name: "Comment",
            scope: "html.doctype",
            settings: {
                foreground: "#5c6370",
                fontStyle: "italic",
            },
        },
        {
            name: "String",
            scope: "string",
            settings: {
                foreground: "#98c379",
            },
        },
        {
            name: "Embedded String Begin and End",
            scope: ["string.embedded.begin", "string.embedded.end"],
            settings: {
                foreground: "#e06c75",
            },
        },
        {
            name: "Embedded String",
            scope: "string.embedded",
            settings: {
                foreground: "#56b6c2",
            },
        },
        {
            name: "Number",
            scope: "constant.numeric",
            settings: {
                foreground: "#d19a66",
            },
        },
        {
            name: "Built-in constant",
            scope: "constant.language",
            settings: {
                foreground: "#d19a66",
            },
        },
        {
            name: "User-defined constant",
            scope: ["constant.character", "constant.other"],
            settings: {
                foreground: "#d19a66",
            },
        },
        {
            name: "Language Variable",
            scope: "variable.language",
            settings: {
                foreground: "#c678dd",
            },
        },
        {
            name: "Variable",
            scope: ["variable.readwrite", "variable.block", "variable.support"],
            settings: {
                foreground: "#e06c75",
            },
        },
        {
            name: "Variable",
            scope: "variable.readwrite.var-single-variable.js",
            settings: {
                foreground: "#d19a66",
            },
        },
        {
            name: "Variable",
            scope: "variable.readwrite.js",
            settings: {
                foreground: "#abb2bf",
            },
        },
        {
            name: "Keyword",
            scope: [
                "keyword",
                "keyword.operator.logical",
                "keyword.operator.constructor",
                "keyword.operator.new",
            ],
            settings: {
                foreground: "#c678dd",
            },
        },
        {
            name: "Keyword Operator",
            scope: "keyword.operator",
            settings: {
                foreground: "#61afef",
            },
        },
        {
            name: "Storage",
            scope: "storage",
            settings: {
                fontStyle: "",
                foreground: "#c678dd",
            },
        },
        {
            name: "Storage type",
            scope: "storage.type.function",
            settings: {
                foreground: "#c678dd",
            },
        },
        {
            name: "Class name",
            scope: ["entity.name.class", "entity.name.module", "entity.name.type"],
            settings: {
                foreground: "#e5c07b",
            },
        },
        {
            name: "Inherited class",
            scope: "entity.other.inherited-class",
            settings: {
                foreground: "#98c379",
            },
        },
        {
            name: "Tag name",
            scope: "entity.name.tag",
            settings: {
                fontStyle: "",
                foreground: "#e06c75",
            },
        },
        {
            name: "Tag attribute",
            scope: "entity.other.attribute-name",
            settings: {
                fontStyle: "",
                foreground: "#d19a66",
            },
        },
        {
            name: "Function name",
            scope: "entity.name.function",
            settings: {
                fontStyle: "",
                foreground: "#61afef",
            },
        },
        {
            name: "Function argument",
            scope: "variable.parameter",
            settings: {
                fontStyle: "italic",
                foreground: "#e06c75",
            },
        },
        {
            name: "Function call",
            scope: "entity.name.function-call",
            settings: {
                fontStyle: "",
                foreground: "#abb2bf",
            },
        },
        {
            name: "Builtin Functions",
            scope: ["function.support.builtin", "function.support.core"],
            settings: {
                fontStyle: "",
                foreground: "#56b6c2",
            },
        },
        {
            name: "Library function",
            scope: "support.function",
            settings: {
                foreground: "#56b6c2",
            },
        },
        {
            name: "Library constant",
            scope: "support.constant",
            settings: {
                fontStyle: "",
                foreground: "#e5c07b",
            },
        },
        {
            name: "Library class/type",
            scope: "support.class",
            settings: {
                foreground: "#e5c07b",
            },
        },
        {
            name: "Library type",
            scope: "support.type",
            settings: {
                foreground: "#e06c75",
            },
        },
        {
            name: "Json Property",
            scope: "support.dictionary.json",
            settings: {
                foreground: "#e06c75",
            },
        },
        {
            name: "StyleSheet Property name",
            scope: [
                "support.type.property-name.css",
                "support.type.property-name.scss",
                "support.type.property-name.less",
                "support.type.property-name.sass",
            ],
            settings: {
                foreground: "#abb2bf",
            },
        },
        {
            name: "StyleSheet Property value",
            scope: [
                "support.constant.css",
                "support.constant.scss",
                "support.constant.less",
                "support.constant.sass",
            ],
            settings: {
                foreground: "#56b6c2",
            },
        },
        {
            name: "StyleSheet Variable",
            scope: ["variable.css", "variable.scss", "variable.less", "variable.sass"],
            settings: {
                foreground: "#e06c75",
            },
        },
        {
            name: "StyleSheet Variable String",
            scope: [
                "variable.css.string",
                "variable.scss.string",
                "variable.less.string",
                "variable.sass.string",
            ],
            settings: {
                foreground: "#98c379",
            },
        },
        {
            name: "StyleSheet Unit",
            scope: ["unit.css", "unit.scss", "unit.less", "unit.sass"],
            settings: {
                foreground: "#d19a66",
            },
        },
        {
            name: "StyleSheet Function",
            scope: ["function.css", "function.scss", "function.less", "function.sass"],
            settings: {
                foreground: "#56b6c2",
            },
        },
        {
            name: "Other variable",
            scope: ["variable.other.property", "variable.other.object", "variable.other.block"],
            settings: {
                foreground: "#e06c75",
            },
        },
        {
            name: "Pug/Jade Import",
            scope: ["jade.import.variable", "pug.import.variable"],
            settings: {
                foreground: "#e06c75",
            },
        },
        {
            name: "Invalid",
            scope: "invalid",
            settings: {
                background: "#c678dd",
                fontStyle: "",
                foreground: "#F8F8F0",
            },
        },
        {
            name: "Invalid deprecated",
            scope: "invalid.deprecated",
            settings: {
                background: "#56b6c2",
                foreground: "#F8F8F0",
            },
        },
        {
            name: "JSON String",
            scope: "structure.dictionary.property-name.json",
            settings: {
                foreground: "#e06c75",
            },
        },
        {
            name: "Link",
            scope: "string.detected-link",
            settings: {
                foreground: "#c678dd",
            },
        },
        {
            name: "diff.header",
            scope: ["meta.diff", "meta.diff.header"],
            settings: {
                foreground: "#75715E",
            },
        },
        {
            name: "diff.deleted",
            scope: "markup.deleted",
            settings: {
                foreground: "#c678dd",
            },
        },
        {
            name: "diff.inserted",
            scope: "markup.inserted",
            settings: {
                foreground: "#e5c07b",
            },
        },
        {
            name: "diff.changed",
            scope: "markup.changed",
            settings: {
                foreground: "#98c379",
            },
        },
        {
            scope: "constant.numeric.line-number.find-in-files - match",
            settings: {
                foreground: "#56b6c2A0",
            },
        },
        {
            scope: "entity.name.filename.find-in-files",
            settings: {
                foreground: "#98c379",
            },
        },
    ],
    colors: {
        "activityBar.background": "#2F333D",
        "activityBar.foreground": "#D7DAE0",
        "activityBarBadge.background": "#528bff",
        "activityBarBadge.foreground": "#F8FAFD",
        "button.background": "#528bff",
        "dropdown.background": "#1d1f23",
        "diffEditor.insertedTextBackground": "#00809B33",
        "dropdown.border": "#181A1F",
        "editor.background": "#282c34",
        "editorError.foreground": "#c24038",
        "editorRuler.foreground": "#484848",
        "editor.lineHighlightBackground": "#383E4A",
        "editor.selectionBackground": "#3E4451",
        "editorCursor.foreground": "#f8f8f0",
        "editor.editor.findMatchBackground": "#42557B",
        "editor.findMatchHighlightBackground": "#314365",
        "editorGroup.background": "#181A1F",
        "editorGroup.border": "#181A1F",
        "editorGroupHeader.tabsBackground": "#21252B",
        "editorIndentGuide.background": "#3B4048",
        "editorLineNumber.foreground": "#495162",
        "editorWhitespace.foreground": "#3B4048",
        "editorHoverWidget.background": "#21252B",
        "editorHoverWidget.border": "#181A1F",
        "editorSuggestWidget.background": "#21252B",
        "editorSuggestWidget.border": "#181A1F",
        "editorSuggestWidget.selectedBackground": "#2c313a",
        "editorWidget.background": "#21252B",
        "input.background": "#1d1f23",
        "list.activeSelectionBackground": "#2c313a",
        "list.activeSelectionForeground": "#d7dae0",
        "list.focusBackground": "#383E4A",
        "list.hoverBackground": "#292d35",
        "list.highlightForeground": "#C5C5C5",
        "list.inactiveSelectionBackground": "#2c313a",
        "list.inactiveSelectionForeground": "#d7dae0",
        "notification.background": "#21252b",
        "scrollbarSlider.background": "#4E566680",
        "scrollbarSlider.activeBackground": "#747D9180",
        "scrollbarSlider.hoverBackground": "#5A637580",
        "sideBar.background": "#21252b",
        "sideBarSectionHeader.background": "#282c34",
        "statusBar.background": "#21252B",
        "statusBar.foreground": "#9da5b4",
        "statusBarItem.hoverBackground": "#2c313a",
        "statusBar.noFolderBackground": "#21252B",
        "statusBar.debuggingBackground": "#21252B",
        "tab.activeBackground": "#2c313a",
        "tab.border": "#181A1F",
        "tab.inactiveBackground": "#21252B",
        "titleBar.activeBackground": "#282c34",
        "titleBar.activeForeground": "#9da5b4",
        "titleBar.inactiveBackground": "#282C34",
        "titleBar.inactiveForeground": "#6B717D",
    },
    name: "One Dark Theme",
};

//#endregion

export const OneDark: editor.IStandaloneThemeData = {
    base: "vs-dark",
    inherit: true,
    rules: createRules(OneDarkTheme.tokenColors),
    colors: OneDarkTheme.colors,
};
