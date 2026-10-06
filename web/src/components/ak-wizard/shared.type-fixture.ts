// Type-level regression fixture for goauthentik/authentik#22226.
//
// `lit-html` ships `DirectiveResult` as an empty interface, which silently
// accepts any non-nullish value — including a forgotten-`()` label factory
// reference. The `LabelFactory` brand combined with the `_$litDirective$`
// augmentation on `DirectiveResult` (see `src/elements/types.ts`) closes that
// gap. The `@ts-expect-error` lines below pin the closure in place: if either
// guard regresses, the comments turn into "unused @ts-expect-error" errors and
// `npm run lint:types` fails.
//
// This file is intentionally side-effect-free and is not imported anywhere; it
// exists solely so `tsc` evaluates the assertions below.

import { SlottedTemplateResult } from "#elements/types";

import { ButtonKindLabelRecord } from "#components/ak-wizard/shared";

function returnsForgottenCall(): SlottedTemplateResult | null {
    // @ts-expect-error A bare label-factory reference must not be assignable to
    // `SlottedTemplateResult`; the call site forgot the `()`.
    return ButtonKindLabelRecord.close;
}

function returnsCalledFactory(): SlottedTemplateResult | null {
    return ButtonKindLabelRecord.close();
}

export const _fixtures = [returnsForgottenCall, returnsCalledFactory] as const;
