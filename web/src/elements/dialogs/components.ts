// import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

// import {
//     lookupElementConstructor,
//     modalInvoker,
//     ModelFormLikeConstructor,
// } from "#elements/dialogs/directives";
// import type { ModalTemplate } from "#elements/dialogs/invokers";
// import type { DialogInit, TransclusionElementConstructor } from "#elements/dialogs/shared";
// import type { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

// import { msg, str } from "@lit/localize";
// import { html } from "lit-html";

// export interface NewModelButtonProps {
//     kind?: "primary" | "secondary" | "tertiary";
// }

// /**
//  * A helper function to render a button that opens a **modal** for creating a new **model** instance.
//  *
//  * @param factory A custom element constructor or a function that returns a template result.
//  * @param buttonProps Properties to customize the appearance of the button.
//  * @param modalProps Properties to pass to the custom element constructor when the factory is a constructor.
//  * @param options Initialization options for the modal dialog.
//  */
// export function ModalInvokerButton<T extends ModalTemplate | TransclusionElementConstructor>(
//     factory: T,
//     modalProps?: T extends TransclusionElementConstructor
//         ? LitPropertyRecord<InstanceType<T>> | null
//         : null,
//     buttonProps?: NewModelButtonProps | null,
//     options?: DialogInit,
// ): SlottedTemplateResult {
//     const { kind = "primary" } = buttonProps ?? {};

//     const { verboseName, createLabel = msg("New") } = factory as TransclusionElementConstructor;
//     const label = verboseName
//         ? msg(str`${createLabel} ${verboseName}`, {
//               id: "invoker.label.modifier-noun",
//           })
//         : createLabel;

//     return html`<button
//         class="pf-c-button pf-m-${kind}"
//         ${modalInvoker(factory, modalProps, options)}
//     >
//         ${label}
//     </button>`;
// }

// /**
//  * A helper function to render a button that opens a modal for editing an existing model instance.
//  *
//  * @param factory A custom element constructor or a function that returns a template result.
//  * @param instancePk The primary key of the instance to edit.
//  * @param itemName An optional name of the item to include in the button's aria-label and tooltip.
//  * @param modalProps Properties to pass to the custom element constructor when the factory is a constructor.
//  * @param options Initialization options for the modal dialog.
//  */
// export function IconEditButton<T extends TransclusionElementConstructor>(
//     factory: T,
//     instancePk?: string | number | null,
//     itemName?: string | null,
//     modalProps?: T extends TransclusionElementConstructor
//         ? LitPropertyRecord<InstanceType<T>>
//         : null,
//     options?: DialogInit,
// ): SlottedTemplateResult {
//     const noun = (factory as TransclusionElementConstructor).verboseName ?? msg("Entity");
//     const label = itemName
//         ? msg(str`Edit "${itemName}" ${noun}`, {
//               id: "entity.edit.named",
//           })
//         : msg(str`Edit ${noun}`, {
//               id: "entity.edit",
//           });

//     const props: LitPropertyRecord<ModelFormLikeConstructor> = { ...modalProps, instancePk };

//     return html`<button
//         type="button"
//         aria-label=${label}
//         class="pf-c-button pf-m-plain"
//         ${modalInvoker(factory, props as unknown as undefined, options)}
//     >
//         <pf-tooltip position="top" content=${msg("Edit")}>
//             <i aria-hidden="true" class="fas fa-edit"></i>
//         </pf-tooltip>
//     </button>`;
// }

// /**
//  * A helper function to render an edit button by looking up a custom element constructor based on a tag name.
//  *
//  * @param tagName The tag name of the custom element to look up and render in the modal.
//  * @param instancePk The primary key of the instance to edit.
//  * @param itemName An optional name of the item to include in the button's aria-label and tooltip.
//  * @param modalProps Properties to pass to the custom element constructor when found.
//  * @param options Initialization options for the modal dialog.
//  *
//  * @throws {TypeError} If no custom element is defined for the given tag name.
//  *
//  * @see {@link IconEditButton} for the underlying button rendering logic.
//  */
// export function IconEditButtonByTagName<T extends object = object>(
//     tagName: string,
//     instancePk?: string | number | null,
//     itemName?: string | null,
//     modalProps?: LitPropertyRecord<T> | null,
//     options?: DialogInit,
// ): SlottedTemplateResult {
//     const Constructor = lookupElementConstructor(tagName);

//     return IconEditButton(
//         Constructor,
//         instancePk,
//         itemName,
//         modalProps as unknown as undefined,
//         options,
//     );
// }
