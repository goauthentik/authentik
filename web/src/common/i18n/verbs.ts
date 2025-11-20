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
        past: () =>
            msg("Created", {
                id: "action.created",
                desc: "Past tense command form verb 'created'",
            }),
        present: () =>
            msg("Create", {
                id: "action.create",
                desc: "Present tense command form verb 'Create'",
            }),
    },

    add: {
        past: () =>
            msg("Added", {
                id: "action.added",
                desc: "Past tense command form verb 'added'",
            }),
        present: () =>
            msg("Add", {
                id: "action.add",
                desc: "Present tense command form verb 'Add'",
            }),
    },

    generate: {
        past: () =>
            msg("Generated", {
                id: "action.generated",
                desc: "Past tense command form verb 'generated'",
            }),
        present: () =>
            msg("Generate", {
                id: "action.generate",
                desc: "Present tense command form verb 'Generate'",
            }),
    },

    //#endregion

    //#region Destructive

    delete: {
        past: () =>
            msg("Deleted", {
                id: "action.deleted",
                desc: "Past tense command form verb 'deleted'",
            }),
        present: () =>
            msg("Delete", {
                id: "action.delete",
                desc: "Present tense command form verb 'Delete'",
            }),
    },

    revoke: {
        past: () =>
            msg("Revoked", {
                id: "action.revoked",
                desc: "Past tense command form verb 'revoked'",
            }),
        present: () =>
            msg("Revoke", {
                id: "action.revoke",
                desc: "Present tense command form verb 'Revoke'",
            }),
    },

    remove: {
        past: () =>
            msg("Removed", {
                id: "action.removed",
                desc: "Past tense command form verb 'removed'",
            }),
        present: () =>
            msg("Remove", {
                id: "action.remove",
                desc: "Present tense command form verb 'Remove'",
            }),
    },

    //#endregion

    //#region Directive

    import: {
        past: () =>
            msg("Imported", {
                id: "action.imported",
                desc: "Past tense command form verb 'imported'",
            }),
        present: () =>
            msg("Import", {
                id: "action.import",
                desc: "Present tense command form verb 'Import'",
            }),
    },

    send: {
        past: () =>
            msg("Sent", {
                id: "action.sent",
                desc: "Past tense command form verb 'sent'",
            }),
        present: () =>
            msg("Send", {
                id: "action.send",
                desc: "Present tense command form verb 'Send'",
            }),
    },

    assign: {
        past: () =>
            msg("Assigned", {
                id: "action.assigned",
                desc: "Past tense command form verb 'assigned'",
            }),
        present: () =>
            msg("Assign", {
                id: "action.assign",
                desc: "Present tense command form verb 'Assign'",
            }),
    },

    trigger: {
        past: () =>
            msg("Triggered", {
                id: "action.triggered",
                desc: "Past tense command form verb 'triggered'",
            }),
        present: () =>
            msg("Trigger", {
                id: "action.trigger",
                desc: "Present tense command form verb 'Trigger'",
            }),
    },

    impersonate: {
        past: () =>
            msg("Impersonated", {
                id: "action.impersonated",
                desc: "Past tense command form verb 'impersonated'",
            }),
        present: () =>
            msg("Impersonate", {
                id: "action.impersonate",
                desc: "Present tense command form verb 'Impersonate'",
            }),
    },

    //#endregion

    //#region Modificative

    edit: {
        past: () =>
            msg("Edited", {
                id: "action.edited",
                desc: "Past tense command form verb 'edited'",
            }),
        present: () =>
            msg("Edit", {
                id: "action.edit",
                desc: "Present tense command form verb 'Edit'",
            }),
    },

    update: {
        past: () =>
            msg("Updated", {
                id: "action.updated",
                desc: "Past tense command form verb 'updated'",
            }),
        present: () =>
            msg("Update", {
                id: "action.update",
                desc: "Present tense command form verb 'Update'",
            }),
    },

    save: {
        past: () =>
            msg("Saved", {
                id: "action.saved",
                desc: "Past tense command form verb 'saved'",
            }),
        present: () =>
            msg("Save", {
                id: "action.save",
                desc: "Present tense command form verb 'Save'",
            }),
    },

    apply: {
        past: () =>
            msg("Applied Changes", {
                id: "action.applied-changes",
                desc: "Past tense command form verb 'apply changes'",
            }),
        present: () =>
            msg("Apply Changes", {
                id: "action.apply-changes",
                desc: "Present tense command form verb 'Apply Changes'",
            }),
    },

    //#endregion
};

export type ActionTenseRecord = typeof ActionTenseRecord;
