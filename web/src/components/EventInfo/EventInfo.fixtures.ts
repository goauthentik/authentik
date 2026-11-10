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

// Event.from_http (authentik/events/models.py)
const httpRequest = {
    path: "/api/v3/core/users/",
    method: "GET",
    args: {},
    user_agent: "Mozilla/5.0",
};

// model_to_dict (authentik/events/utils.py); `pk` can be an int or a UUID string.
const flowModel = {
    pk: "c4f8e2a0-7b1d-4e9f-a3c5-6d8b0e2f4a1c",
    app: "authentik_flows",
    name: "Welcome to authentik!",
    model_name: "flow",
};

const policyContext = {
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
        obj: flowModel,
        context: { auth_method: "password" },
        debug: false,
    },
};

export const fixtures = {
    modelCreated: sampleEvent(EventActions.ModelCreated, {
        model: {
            pk: 1,
            app: "authentik_stages_password",
            name: "Password",
            model_name: "passworddevice",
        },
        http_request: httpRequest,
    }),

    // AuditMiddleware.diff (authentik/enterprise/audit/middleware.py)
    modelUpdated: sampleEvent(EventActions.ModelUpdated, {
        model: {
            pk: 4,
            app: "authentik_core",
            name: "authentik Default Admin",
            model_name: "user",
        },
        diff: { name: { previous_value: "old", new_value: "new" } },
        http_request: httpRequest,
    }),

    // M2M from AuditMiddleware.m2m_changed_handler: `{related_name: {add|remove: [pk, ...]}}` or
    // `{related_name: {clear: true}}`.
    modelUpdatedM2M: sampleEvent(EventActions.ModelUpdated, {
        model: { pk: 7, app: "authentik_core", name: "brains-eaters", model_name: "group" },
        diff: {
            users: { add: ["3", "5"] },
            roles: { remove: ["9"] },
            parents: { clear: true },
        } as unknown as EventContext,
    }),

    modelDeleted: sampleEvent(EventActions.ModelDeleted, {
        model: { pk: 5, app: "authentik_core", name: "Doomed!", model_name: "user" },
    }),

    // AuthorizationFlowInitView (authentik/providers/oauth2/views/authorize.py)
    authorizeApplication: sampleEvent(EventActions.AuthorizeApplication, {
        authorized_application: {
            pk: "7d1e3a5c-9b2f-4c8d-a6e0-1f3b5d7c9e2a",
            app: "authentik_core",
            name: "Brain Bank",
            model_name: "application",
        },
        flow: flowModel.pk,
        scopes: "openid profile email",
        http_request: httpRequest,
    }),

    // send_mail (authentik/stages/email/tasks.py)
    emailSent: sampleEvent(EventActions.EmailSent, {
        message: "Email to guests@mighty.authentik.io sent",
        subject: "A mighty subject",
        from_email: "subject@mighty.authentik.io",
        to_email: ["guests@mighty.authentik.io"],
        body: '<html><body><img src="cid:logo" alt="logo"><p>De apocalypsi gorger omero undead survivor dictum mauris.</p></body></html>',
    }),

    // TokenViewSet.view_key (authentik/core/api/tokens.py)
    secretView: sampleEvent(EventActions.SecretView, {
        secret: {
            pk: "439ac0de",
            app: "authentik_core",
            name: "ifyoucanreadthisyouresittingtooclose",
            model_name: "token",
        },
        http_request: httpRequest,
    }),

    systemException: sampleEvent(EventActions.SystemException, {
        message:
            "Traceback (most recent call last):\n  File \"brains.py\", line 1\nKeyError: 'brains'",
        http_request: httpRequest,
    }),

    // TaskLogMiddleware (authentik/tasks/middleware.py); `exception` omitted.
    systemTaskException: sampleEvent(EventActions.SystemTaskException, {
        message: "Task authentik.blueprints.v1.tasks.apply_blueprint encountered an error",
        actor: "authentik.blueprints.v1.tasks.apply_blueprint",
    }),

    configurationWarning: sampleEvent(EventActions.ConfigurationWarning, {
        message: "Warning! Brains!",
    }),

    configurationError: sampleEvent(EventActions.ConfigurationError, {
        message: "Error! Missing Brains!",
    }),

    // update_latest_version (authentik/admin/tasks.py)
    updateAvailable: sampleEvent(EventActions.UpdateAvailable, {
        message: "New version 666.6.6 available!",
        new_version: "666.6.6",
        changelog: "https://docs.goauthentik.io/docs/releases/666.6",
        reason: "",
    }),

    // on_user_logged_in (authentik/events/signals.py), password login.
    login: sampleEvent(EventActions.Login, {
        auth_method: "password",
        auth_method_args: {},
        http_request: httpRequest,
    }),

    // on_user_logged_in stores the source under PLAN_CONTEXT_SOURCE, `source`.
    loginWithSource: sampleEvent(EventActions.Login, {
        source: {
            pk: "e2a4c6b8-0d1f-4e3a-9c5b-7d9f1b3e5a7c",
            app: "authentik_sources_oauth",
            name: "GitHub",
            model_name: "oauthsource",
        },
        http_request: httpRequest,
    }),

    // on_login_failed (authentik/events/signals.py)
    loginFailed: sampleEvent(EventActions.LoginFailed, {
        username: "j-random-hacker",
        stage: {
            pk: "b1d3f5a7-9c2e-4a6b-8d0f-2e4a6c8b0d1f",
            app: "authentik_stages_password",
            name: "default-authentication-password",
            model_name: "passwordstage",
        },
        http_request: httpRequest,
    }),

    logout: sampleEvent(EventActions.Logout, {}),

    logoutWithContext: sampleEvent(EventActions.Logout, { http_request: httpRequest }),

    // ExpressionEvaluator.handle_error (authentik/core/expression/evaluator.py)
    propertyMappingException: sampleEvent(EventActions.PropertyMappingException, {
        message: "Failed to execute property mapping",
        expression: 'return {"name": request.user.nmae}',
    }),

    // create_policy_event (authentik/policies/process.py)
    policyException: sampleEvent(EventActions.PolicyException, {
        message: "Policy failed to execute",
        ...policyContext,
    }),

    policyExecution: sampleEvent(EventActions.PolicyExecution, {
        message: "Policy Execution",
        ...policyContext,
        result: { passing: true, messages: [] },
    }),

    // Dry-run variant
    policyExecutionDryRun: sampleEvent(EventActions.PolicyExecution, {
        message: "Policy Execution (dry run)",
        ...policyContext,
        result: { passing: false, messages: ["Brains required."], raw_result: false },
        dry_run: true,
        cached: false,
    }),

    // fall through to renderDefault.
    unhandled: sampleEvent(EventActions.SuspiciousRequest, {
        message: "Brains detected in an unexpected place",
        http_request: httpRequest,
    }),
} satisfies Record<string, EventWithContext>;

export type EventInfoFixture = keyof typeof fixtures;
