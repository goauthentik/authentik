import { msg } from "@lit/localize";

export interface TenseRecord {
    past: string;
    present: string;
}

export const ActionTenseRecord = {
    //#region Constructive

    create: {
        past: msg("created"),
        present: msg("create"),
    },

    add: {
        past: msg("added"),
        present: msg("add"),
    },

    generate: {
        past: msg("generated"),
        present: msg("generate"),
    },

    //#endregion

    //#region Destructive

    $delete: {
        past: msg("deleted"),
        present: msg("delete"),
    },

    revoke: {
        past: msg("revoked"),
        present: msg("revoke"),
    },

    remove: {
        past: msg("removed"),
        present: msg("remove"),
    },

    //#endregion

    //#region Directive

    $import: {
        past: msg("imported"),
        present: msg("import"),
    },

    send: {
        past: msg("sent"),
        present: msg("send"),
    },

    assign: {
        past: msg("assigned"),
        present: msg("assign"),
    },

    trigger: {
        past: msg("triggered"),
        present: msg("trigger"),
    },

    impersonate: {
        past: msg("impersonated"),
        present: msg("impersonate"),
    },

    //#endregion

    //#region Modificative

    update: {
        past: msg("updated"),
        present: msg("update"),
    },

    save: {
        past: msg("saved"),
        present: msg("save"),
    },

    //#endregion
} as const satisfies Record<string, TenseRecord>;

export type ActionTenseRecord = typeof ActionTenseRecord;

export type ActionName = keyof ActionTenseRecord;
