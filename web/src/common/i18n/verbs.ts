import { msg } from "@lit/localize";

export interface TenseRecord {
    past: () => string;
    present: () => string;
}

export type ActionName =
    | "send"
    | "assign"
    | "trigger"
    | "impersonate"
    | "edit"
    | "update"
    | "save"
    | "apply"
    | "create"
    | "add"
    | "generate"
    | "delete"
    | "revoke"
    | "remove"
    | "import";

export const ActionTenseRecord: Record<ActionName, TenseRecord> = {
    //#region Constructive

    create: {
        past: () => msg("Created"),
        present: () => msg("Create"),
    },

    add: {
        past: () => msg("Added"),
        present: () => msg("Add"),
    },

    generate: {
        past: () => msg("Generated"),
        present: () => msg("Generate"),
    },

    //#endregion

    //#region Destructive

    delete: {
        past: () => msg("Deleted"),
        present: () => msg("Delete"),
    },

    revoke: {
        past: () => msg("Revoked"),
        present: () => msg("Revoke"),
    },

    remove: {
        past: () => msg("Removed"),
        present: () => msg("Remove"),
    },

    //#endregion

    //#region Directive

    import: {
        past: () => msg("Imported"),
        present: () => msg("Import"),
    },

    send: {
        past: () => msg("Sent"),
        present: () => msg("Send"),
    },

    assign: {
        past: () => msg("Assigned"),
        present: () => msg("Assign"),
    },

    trigger: {
        past: () => msg("Triggered"),
        present: () => msg("Trigger"),
    },

    impersonate: {
        past: () => msg("Impersonated"),
        present: () => msg("Impersonate"),
    },

    //#endregion

    //#region Modificative

    edit: {
        past: () => msg("Edited"),
        present: () => msg("Edit"),
    },

    update: {
        past: () => msg("Updated"),
        present: () => msg("Update"),
    },

    save: {
        past: () => msg("Saved"),
        present: () => msg("Save"),
    },

    apply: {
        past: () => msg("Applied Changes"),
        present: () => msg("Apply Changes"),
    },

    //#endregion
};

export type ActionTenseRecord = typeof ActionTenseRecord;
