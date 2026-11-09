import { EventActions } from "@goauthentik/api";
import { EventContext, EventModel, EventWithContext } from "#common/events";

const sampleModel: EventModel = {
    pk: "8f6c0d2e-…",
    name: "Example Application",
    app: "authentik_core",
    model_name: "application",
};

const sampleEvent = (action: EventActions, context: EventContext = {}): EventWithContext => ({
    pk: "a1b2…",
    app: "authentik_events",
    created: new Date("2026-11-09T12:00:00Z"),
    action,
    context,
    user: { pk: 1, username: "akadmin", email: "admin@example.com" },
});

const modelCreated = sampleEvent(EventActions.ModelCreated, {
    "pk": 1,
    "app": "authentik_stages_password",
    "name": "Password",
    "model_name": "passworddevice"
});

const modelUpdated = sampleEvent(EventActions.ModelUpdated, {
    "pk": 4,
    "app": "authentik_core",
    "name": "authentik Default Admin",
    "model_name": "user"
});

const modelDeleted = sampleEvent(EventAction.ModelDeleted, {
    "pk": 5,
    "app": "authentik_core",
    "name": "Doomed!",
    "model_name": "user"
});





│ ModelCreated / Updated / Deleted │ model, diff (optional)                                                                  │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ AuthorizeApplication             │ authorized_application, flow (calls the API, so stub it or leave it out)                │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ EmailSent                        │ body, message, subject, from_email, to_email: string[]                                  │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ SecretView                       │ secret                                                                                  │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ SystemException                  │ message, http_request.{method,path} (optional)                                          │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ PropertyMappingException         │ message or error, expression                                                            │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ PolicyException                  │ binding, request.{obj,context}, message or error                                        │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ PolicyExecution                  │ the same as PolicyException, plus result.{passing,messages,raw_result}, dry_run, cached │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ ConfigurationWarning / Error     │ message                                                                                 │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ UpdateAvailable                  │ new_version, changelog (optional)                                                       │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ Login                            │ using_source (optional; this decides which branch renders)                              │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ LoginFailed                      │ username                                                                                │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ Logout                           │ an empty context, or a non-empty one for the fallback                                   │
  ├──────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────┤
  │ SystemTaskException              │ message
