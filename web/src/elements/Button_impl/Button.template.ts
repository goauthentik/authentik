import { ifPresent } from "#elements/utils/attributes";

import { html } from "lit";

interface ButtonButtonProps {
    disabled: boolean;
    type?: string;
    name?: string;
    value?: string;
    onClick: (ev: MouseEvent) => void;
}

type ButtonLinkProps = Pick<ButtonButtonProps, "disabled" | "onClick"> & {
    href: string;
    target?: string;
    rel?: string;
    download?: string;
};

/**
 * @remarks
 * The ARIA rules for disabled links specifies that "to communicate a link as ‘disabled,’ remove
 * the `href` attribute and style accordingly." Hence the `href=${ifDefined(...)}`.
 *
 * @see {@link https://www.w3.org/TR/html-aria/#example-communicate-a-disabled-link-with-aria | ARIA Disabled Link Rules}
 */

/**
 * @remarks
 *
 * The distinction here is not just functional; by having distinct `[part]` definitions, we allow
 * customizers to target links *or* buttons, if they so choose.
 */

export function linkTemplate(props: ButtonLinkProps) {
    const { href, target, disabled, download, rel, onClick } = props;
    return html`<a
        id="main"
        href=${ifPresent(disabled ? null : href)}
        part="anchor"
        target="${ifPresent(target)}"
        ?disabled=${disabled}
        download=${ifPresent(download)}
        rel=${ifPresent(rel)}
        tabindex=${disabled ? -1 : 0}
        @click=${onClick}
        ><slot></slot
    ></a>`;
}

export function buttonTemplate(props: ButtonButtonProps) {
    const { disabled, type, name, value, onClick } = props;
    return html`<button
        id="main"
        part="button"
        ?disabled=${disabled}
        type=${ifPresent(type)}
        name=${ifPresent(name)}
        value=${ifPresent(value)}
        @click=${onClick}
    >
        <slot></slot>
    </button>`;
}
