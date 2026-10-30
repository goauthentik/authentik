import "#flow/stages/authenticator_email/AuthenticatorEmailStage";
import "#flow/stages/authenticator_validate/AuthenticatorValidateStage";
import "#flow/stages/authenticator_validate/AuthenticatorValidateStageCode";
import { StageHost } from "#flow/types";

import { DeviceClassesEnum, FlowsApi } from "@goauthentik/api";

import { afterEach, describe, expect, it, vi } from "vitest";

const mounted: HTMLElement[] = [];

afterEach(() => {
    for (const element of mounted.splice(0)) element.remove();
});

for (const kind of ["setup", "validation"] as const) {
    describe(`${kind} resend button`, () => {
        function mount(send: () => Promise<boolean>) {
            const stage =
                kind === "setup"
                    ? document.createElement("ak-stage-authenticator-email")
                    : document.createElement("ak-stage-authenticator-validate-code");

            stage.host = { submit: send, resendSelectedChallenge: send } as unknown as StageHost;

            stage.challenge = {
                email: "***@example.com",
                emailRequired: false,
                pendingUser: "",
                pendingUserAvatar: "",
            };

            if ("deviceChallenge" in stage) {
                stage.deviceChallenge = {
                    deviceClass: DeviceClassesEnum.Email,
                    deviceUid: "test-email",
                    lastUsed: new Date(),
                    challenge: {},
                };
            }

            document.body.append(stage);
            mounted.push(stage);

            return stage;
        }

        it("shows sending, then a disabled success state before allowing another send", async () => {
            let resolve!: (sent: boolean) => void;

            const send = vi.fn(
                () =>
                    new Promise<boolean>((done) => {
                        resolve = done;
                    }),
            );

            const stage = mount(send);
            await stage.updateComplete;

            const button =
                stage.shadowRoot!.querySelector<HTMLButtonElement>('button[name="resend"]')!;

            expect(button.disabled).toBe(false);
            button.click();
            await stage.updateComplete;
            expect(button.disabled).toBe(true);
            expect(button.textContent).toContain("Sending");
            button.click();
            expect(send).toHaveBeenCalledTimes(1);
            resolve(true);
            await vi.waitFor(() => expect(button.textContent).toContain("Code sent"));
            expect(button.disabled).toBe(true);

            expect(stage.shadowRoot!.querySelector('[role="status"]')?.textContent).toContain(
                "Code sent",
            );

            await vi.waitFor(() => expect(button.disabled).toBe(false), { timeout: 18000 });
            expect(button.textContent).toContain("Resend code");
        }, 20000);

        it("does not claim a code was sent when the initial email send was rate limited", async () => {
            const stage = mount(async () => false);

            stage.challenge = {
                ...stage.challenge!,
                responseErrors: {
                    [kind === "setup" ? "non_field_errors" : "selected_challenge"]: [
                        { code: "throttled", string: "Email sending was rate limited." },
                    ],
                },
            };

            await stage.updateComplete;

            expect(stage.shadowRoot!.textContent).not.toMatch(
                /A (verification token|code) has been sent/,
            );
        });

        it("keeps the sent-to hint when an entered code is invalid", async () => {
            const stage = mount(async () => false);

            stage.challenge = {
                ...stage.challenge!,
                responseErrors: { code: [{ code: "invalid", string: "Code does not match" }] },
            };

            await stage.updateComplete;

            expect(stage.shadowRoot!.textContent).toMatch(
                /A (verification token|code) has been sent/,
            );
        });

        it("restores the button without claiming success when the server rejects sending", async () => {
            const stage = mount(async () => false);
            await stage.updateComplete;

            const button =
                stage.shadowRoot!.querySelector<HTMLButtonElement>('button[name="resend"]')!;

            button.click();
            await stage.updateComplete;

            await vi.waitFor(() => {
                expect(button.disabled).toBe(false);
                expect(button.textContent).toContain("Resend code");
            });

            expect(button.textContent).toContain("Resend code");
            expect(button.textContent).not.toContain("Code sent");
        });
    });
}

describe("validation resend result", () => {
    afterEach(() => vi.restoreAllMocks());

    for (const rejected of [false, true]) {
        it(`reports success=${!rejected} from the actual selection response`, async () => {
            vi.spyOn(FlowsApi.prototype, "flowsExecutorSolve").mockResolvedValue({
                component: "ak-stage-authenticator-validate",
                pendingUser: "",
                pendingUserAvatar: "",
                deviceChallenges: [],
                configurationStages: [],
                responseErrors: {
                    non_field_errors: [{ string: "Empty response", code: "invalid" }],
                    ...(rejected
                        ? { selected_challenge: [{ string: "Rate limited", code: "throttled" }] }
                        : {}),
                },
            });

            const stage = document.createElement("ak-stage-authenticator-validate");
            stage.host = { submit: vi.fn(), loading: false } as unknown as StageHost;

            stage.challenge = {
                component: "ak-stage-authenticator-validate",
                deviceChallenges: [
                    {
                        deviceClass: DeviceClassesEnum.Email,
                        deviceUid: "test-email",
                        lastUsed: new Date(),
                        challenge: {},
                    },
                ],
                configurationStages: [],
                pendingUser: "",
                pendingUserAvatar: "",
            };

            document.body.append(stage);
            mounted.push(stage);
            await stage.updateComplete;
            expect(await stage.resendSelectedChallenge()).toBe(!rejected);
        });
    }
});
