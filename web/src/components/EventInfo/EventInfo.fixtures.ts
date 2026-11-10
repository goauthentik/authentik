import { EventContext, EventWithContext } from "#common/events";

import { EventActions } from "@goauthentik/api";

const sampleEvent = (action: EventActions, context: EventContext = {}): EventWithContext => ({
    pk: "a1b2",
    app: "authentik_events",
    created: new Date("2026-11-09T12:00:00Z"),
    action,
    context,
    user: { pk: 1, username: "akadmin", email: "admin@example.com" },
});

const fixtureCollection = [
    sampleEvent(EventActions.ModelCreated, {
        model: {
            pk: 1,
            app: "authentik_stages_password",
            name: "Password",
            model_name: "passworddevice",
        },
    }),

    sampleEvent(EventActions.ModelUpdated, {
        model: {
            pk: 4,
            app: "authentik_core",
            name: "authentik Default Admin",
            model_name: "user",
        },
        diff: { name: { previous_value: "old", new_value: "new" } },
    }),

    sampleEvent(EventActions.ModelDeleted, {
        model: {
            pk: 5,
            app: "authentik_core",
            name: "Doomed!",
            model_name: "user",
        },
    }),

    sampleEvent(EventActions.EmailSent, {
        message: "Generic email message",
        subject: "A mighty subject",
        from_email: "subject@mighty.authentik.io",
        to_email: ["guests@mighty.authentik.io"],
        body: "De apocalypsi gorger omero undead survivor dictum mauris. Hi mindless mortuis soulless creaturas, imo evil stalking monstra adventus resi dentevil vultus comedat cerebella viventium.",
    }),

    sampleEvent(EventActions.SecretView, {
        secret: {
            model: "439ac0de",
            app: "authentik_core",
            name: "ifyoucanreadthisyouresittingtooclose",
            model_name: "token",
        },
    }),

    sampleEvent(EventActions.SystemException, {
        message: "Brains!",
    }),

    sampleEvent(EventActions.SystemTaskException, {
        message: "Sprained brains!",
    }),

    sampleEvent(EventActions.ConfigurationWarning, {
        message: "Warning! Brains!",
    }),

    sampleEvent(EventActions.ConfigurationError, {
        message: "Error! Missing Brains!",
    }),

    sampleEvent(EventActions.UpdateAvailable, {
        new_version: "v666.666.666",
        changelog: "https://github.com/goauthentik/authentik/releases/",
    }),

    sampleEvent(EventActions.Login, { username: "j-random-hacker" }),

    sampleEvent(EventActions.Logout, {}),

    // Shape from ExpressionEvaluator.handle_error (authentik/core/expression/evaluator.py)
    sampleEvent(EventActions.PropertyMappingException, {
        message: "Failed to execute property mapping",
        expression: 'return {"name": request.user.nmae}',
    }),

    // Shape from create_policy_event (authentik/policies/process.py)
    sampleEvent(EventActions.PolicyException, {
        message: "Policy failed to execute",
        policy_uuid: "3c1d9a7e5b2f4e0a8d6c4b2a1f0e9d8c",
        binding: {
            pk: "9e2b7c41-5d3a-4f8e-b6a1-2c0d9e8f7a6b",
            app: "authentik_policies",
            name: "Binding from Flow default-authentication-flow #0 to Policy require-brains",
            model_name: "policybinding",
        },
        request: {
            user: { pk: 1, app: "authentik_core", name: "akadmin", model_name: "user" },
            http_request: null,
            obj: {
                pk: "c4f8e2a0-7b1d-4e9f-a3c5-6d8b0e2f4a1c",
                app: "authentik_flows",
                name: "Welcome to authentik!",
                model_name: "flow",
            },
            context: { auth_method: "password" },
            debug: false,
        },
    }),

    // Dry-run variant: exercises the label, raw_result and cached branches of the renderer.
    sampleEvent(EventActions.PolicyExecution, {
        message: "Policy Execution (dry run)",
        policy_uuid: "3c1d9a7e5b2f4e0a8d6c4b2a1f0e9d8c",
        binding: {
            pk: "9e2b7c41-5d3a-4f8e-b6a1-2c0d9e8f7a6b",
            app: "authentik_policies",
            name: "Binding from Flow default-authentication-flow #0 to Policy require-brains",
            model_name: "policybinding",
        },
        request: {
            user: { pk: 1, app: "authentik_core", name: "akadmin", model_name: "user" },
            http_request: null,
            obj: {
                pk: "c4f8e2a0-7b1d-4e9f-a3c5-6d8b0e2f4a1c",
                app: "authentik_flows",
                name: "Welcome to authentik!",
                model_name: "flow",
            },
            context: { auth_method: "password" },
            debug: false,
        },
        result: {
            passing: false,
            messages: ["Brains required."],
            raw_result: false,
        },
        dry_run: true,
        cached: false,
    }),
];

export const fixtures = Object.fromEntries(
    fixtureCollection.map((fixture) => [fixture.action, fixture]),
);
