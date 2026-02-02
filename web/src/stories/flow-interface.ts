import "#flow/FlowExecutor";

import { resolveUITheme } from "#common/theme";
import { DeepPartial } from "#common/types";

import { AKElement } from "#elements/Base";

import { FlowChallengeLike } from "#flow/components/types";

import { ChallengeTypes, ContextualFlowInfoLayoutEnum, UiThemeEnum } from "@goauthentik/api";

import { StoryObj } from "@storybook/web-components";
import { deepmerge } from "deepmerge-ts";
import { StoryAnnotations } from "storybook/internal/csf";

import { html, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-storybook-interface-flow")
export class StoryFlowInterface extends AKElement {
    protected override createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    @property({ type: String, attribute: "slug", useDefault: true })
    public flowSlug = "default-authentication-flow";

    @property({ attribute: false })
    public challenge: ChallengeTypes | null = null;

    #synchronizeTheme = () => {
        this.ownerDocument.documentElement.dataset.themeChoice = resolveUITheme(this.activeTheme);
    };

    public override updated(changed: PropertyValues<this>): void {
        if (changed.has("activeTheme")) {
            this.#synchronizeTheme();
        }
    }

    public override firstUpdated(changed: PropertyValues<this>): void {
        super.firstUpdated(changed);
        this.#synchronizeTheme();
    }

    protected render() {
        return html`
            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer pf-m-collapsed" id="flow-drawer">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                <ak-flow-executor
                                    class="pf-c-login"
                                    .challenge=${this.challenge}
                                ></ak-flow-executor>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

let backgroundSeed = Date.now();
let avatarSeed = backgroundSeed + 1;

function createChallenge<T extends FlowChallengeLike>(
    component: ChallengeTypes["component"],
    overrides?: DeepPartial<T>,
): T {
    const challenge = deepmerge(
        {
            pendingUser: "Jessie Lorem",
            pendingUserAvatar: `https://picsum.photos/seed/${avatarSeed++}/64`,
            flowInfo: {
                title: `<${component}>`,
                layout: ContextualFlowInfoLayoutEnum.Stacked,
                cancelUrl: "",
                background: `https://picsum.photos/seed/${backgroundSeed++}/1920/1080`,
            },
        } satisfies FlowChallengeLike,
        overrides,
    );

    return challenge as T;
}

export function flowFactory<C extends ChallengeTypes["component"]>(
    component: C,
    overrides?: DeepPartial<Extract<ChallengeTypes, { component: C }>>,
    annotations?: StoryAnnotations,
): StoryObj<{ theme: UiThemeEnum }> {
    const challenge = createChallenge<FlowChallengeLike>(component, overrides);

    return {
        argTypes: {
            theme: {
                options: [UiThemeEnum.Automatic, UiThemeEnum.Light, UiThemeEnum.Dark],
                control: {
                    type: "select",
                },
            },
        },

        args: {
            theme: "automatic",
        },

        render: ({ theme }) => {
            return html`<ak-storybook-interface-flow
                theme=${theme}
                .challenge=${{
                    component,
                    ...challenge,
                }}
            >
            </ak-storybook-interface-flow>`;
        },
        ...annotations,
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-storybook-interface-flow": StoryFlowInterface;
    }
}
