import Styles from "./search-select.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

import { torusIndex } from "#common/collections";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { AKRefreshEvent } from "#common/events";

import { listen } from "#elements/decorators/listen";
import { AnchorPositionSupported, placeAnchoredPopover } from "#elements/dialogs/positioning";
import { FormAssociatedElement } from "#elements/forms/form-associated-element";
import {
    SearchSelectActionEvent,
    SearchSelectChangeEvent,
} from "#elements/forms/SearchSelect/events";
import { formatOptionID, SearchSelectSource } from "#elements/forms/SearchSelect/shared";
import { SettlingFormField } from "#elements/forms/settle-form-fields";
import type { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { isFirefox } from "#elements/utils/useragent";

import { ConsoleLogger, Logger } from "#logger/browser";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { live } from "lit/directives/live.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

const UsesAnchorFallback = !AnchorPositionSupported || isFirefox();

interface SearchSelectOption<T> {
    id: string;
    key: string;
    label: string;
    description: SlottedTemplateResult;
    disabled: boolean;
    kind: "object" | "blank" | "action";
    object: T | null;
}

interface SearchSelectOptionGroup<T> {
    name: string;
    options: SearchSelectOption<T>[];
}

/**
 * A form field for choosing one API object, searched as the user types.
 *
 * @remarks
 *   The value is the chosen object's key, as given by its {@linkcode SearchSelectSource}. Set
 *   `selectedObject` alongside it to show the object's label before the first fetch lands.
 * @fires ak-change - The selection changed. `detail.value` is the chosen object.
 * @fires ak-search-select-action - The pinned action item was activated.
 * @csspart input - The text input.
 * @csspart listbox - The popover listing the options.
 */
@customElement("ak-search-select")
export class SearchSelect<T = unknown>
    extends FormAssociatedElement<string, string | null>
    implements SettlingFormField
{
    public static styles: CSSResult[] = [PFFormControl, Styles];

    declare anchorRef: Ref<HTMLInputElement>;
    declare anchor: HTMLInputElement | null;

    //#region Properties

    /**
     * Where the options come from, and how they are presented.
     */
    @property({ attribute: false })
    public source: SearchSelectSource<T> | null = null;

    #value = "";

    /**
     * The key of the chosen object, or an empty string when nothing is chosen.
     */
    @property({ type: String })
    public get value(): string {
        return this.#value;
    }

    public set value(nextValue: string | null | undefined) {
        this.#value = nextValue ?? "";

        if (this.selectedObject && this.#keyOf(this.selectedObject) !== this.#value) {
            this.selectedObject = this.#findObject(this.#value);
        }

        this.#syncFormValue();
    }

    /**
     * The chosen object. Provide it with `value` to label the input before the options load.
     */
    @property({ attribute: false })
    public selectedObject: T | null = null;

    @property({ type: String })
    public label: string | null = null;

    @property({ type: String })
    public placeholder: string | null = msg("Select an object...");

    /**
     * Offer an empty option, so the selection can be cleared.
     */
    @property({ type: Boolean })
    public blankable = false;

    /**
     * The label of the empty option offered by `blankable`.
     */
    @property({ type: String, attribute: "empty-option" })
    public emptyOption: string = "---------";

    /**
     * What the field serializes as when nothing is chosen. Use an empty string for fields that
     * hold text rather than a nullable relation.
     */
    @property({ attribute: false })
    public emptyValue: string | null = null;

    /**
     * Accept typed text as the value when no option matches it.
     */
    @property({ type: Boolean })
    public creatable = false;

    /**
     * The label of a pinned action item, e.g. "Create new...".
     */
    @property({ type: String, attribute: "action-label" })
    public actionLabel: string | null = null;

    //#endregion

    //#region State

    @state()
    protected objects: T[] | null = null;

    @state()
    protected query = "";

    @state()
    protected editing = false;

    @state()
    protected activeKey: string | null = null;

    @state()
    protected loading = false;

    @state()
    protected error: APIError | null = null;

    protected listboxRef = createRef<HTMLElement>();

    protected logger: Logger;

    #refreshRequestID = 0;
    #pendingRefresh: Promise<void> = Promise.resolve();
    #trackingFrame: number | null = null;
    #openAbortController: AbortController | null = null;

    //#endregion

    //#region Lifecycle

    public constructor() {
        super();

        this.logger = ConsoleLogger.prefix(this.localName);
    }

    public override connectedCallback(): void {
        super.connectedCallback();

        this.#syncFormValue();

        if (this.hasUpdated) this.refresh();
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();

        this.#stopTracking();
        this.#openAbortController?.abort();
    }

    public formResetCallback(): void {
        this.value = "";
        this.selectedObject = null;
    }

    public formStateRestoreCallback(state: string): void {
        this.value = state;
    }

    public override updated(changedProperties: PropertyValues): void {
        super.updated(changedProperties);

        if (changedProperties.has("source")) {
            this.refresh();
        }

        if (changedProperties.has("required")) {
            this.#syncFormValue();
        }

        if (changedProperties.has("activeKey") && this.activeKey !== null) {
            this.renderRoot
                .querySelector(`#${CSS.escape(formatOptionID(this.activeKey))}`)
                ?.scrollIntoView({
                    block: "nearest",
                });
        }
    }

    /**
     * The value for the API: `emptyValue` when nothing is chosen, or an empty string for
     * `creatable` fields, which hold free text rather than a relation.
     */
    public toJSON(): string | null {
        return this.value || (this.creatable ? "" : this.emptyValue);
    }

    //#endregion

    //#region Public API

    /**
     * Whether the options popover is showing.
     */
    public get open(): boolean {
        return this.listboxRef.value?.matches(":popover-open") ?? false;
    }

    public show(): void {
        if (this.readOnly || this.disabled || this.open) return;

        this.listboxRef.value?.showPopover({ source: this.anchor ?? undefined });
    }

    public hide(): void {
        if (!this.open) return;

        this.listboxRef.value?.hidePopover();
    }

    /**
     * Fetch the options for the current query.
     */
    public refresh(): Promise<void> {
        const { source } = this;

        if (!source) return Promise.resolve();

        const requestID = ++this.#refreshRequestID;
        this.loading = true;

        const pending = source
            .fetchObjects(this.query || undefined)
            .then((objects) => {
                if (requestID !== this.#refreshRequestID) return;

                this.objects = objects;
                this.error = null;

                if (this.value) {
                    this.selectedObject ??= this.#findObject(this.value);
                } else if (!this.query) {
                    const preselected = source.preselect?.(objects);

                    if (preselected) this.#applySelection(preselected);
                }
            })
            .catch(async (error: unknown) => {
                const parsedError = await parseAPIResponseError(error);

                if (requestID !== this.#refreshRequestID) return;

                this.logger.error("Failed to fetch options", parsedError);
                this.objects = null;
                this.error = parsedError;
            })
            .finally(() => {
                if (requestID === this.#refreshRequestID) {
                    this.loading = false;
                }
            });

        this.#pendingRefresh = pending;

        return pending;
    }

    /**
     * Resolves once the latest fetch has landed and its selection has rendered.
     */
    public get settled(): Promise<void> {
        return this.updateComplete.then(() => {
            const pending = this.#pendingRefresh;

            return pending.then(() =>
                pending === this.#pendingRefresh
                    ? this.updateComplete.then(() => undefined)
                    : this.settled,
            );
        });
    }

    /**
     * Choose an object, or clear the selection with `null`.
     */
    public select(object: T | null): void {
        this.#applySelection(object);
        this.#stopEditing();
        this.hide();
    }

    /**
     * Set the selection and announce it, leaving the popover and any typing as they are.
     */
    #applySelection(object: T | null): void {
        this.selectedObject = object;
        this.value = object ? this.#keyOf(object) : "";

        this.dispatchEvent(new SearchSelectChangeEvent<T>(object));
    }

    //#endregion

    //#region Options

    #keyOf(object: T): string {
        return this.source?.keyOf(object) ?? "";
    }

    #labelOf(object: T): string {
        return this.source?.labelOf(object) ?? "";
    }

    #findObject(key: string): T | null {
        if (!key) return null;

        return this.objects?.find((object) => this.#keyOf(object) === key) ?? null;
    }

    /**
     * The fetched objects, plus the selection when the fetched page does not include it.
     * Left out while searching, so a stale selection doesn't sit atop the results.
     */
    protected get listedObjects(): T[] {
        const objects = this.objects ?? [];
        const { selectedObject } = this;

        if (!selectedObject || this.query) return objects;

        const selectedKey = this.#keyOf(selectedObject);

        return objects.some((object) => this.#keyOf(object) === selectedKey)
            ? objects
            : [selectedObject, ...objects];
    }

    protected get optionGroups(): SearchSelectOptionGroup<T>[] {
        const { source } = this;

        if (!source) return [];

        const objects = this.listedObjects;
        const groups = source.groupBy?.(objects) ?? [["", objects]];

        return groups.map(([name, members]) => ({
            name,
            options: members.map((object) => {
                const key = this.#keyOf(object);

                return {
                    id: formatOptionID(key),
                    key,
                    label: this.#labelOf(object),
                    description: source.describe?.(object) ?? null,
                    disabled: source.isDisabled?.(object) ?? false,
                    kind: "object",
                    object,
                };
            }),
        }));
    }

    protected get blankOption(): SearchSelectOption<T> | null {
        if (!this.blankable || this.query) return null;

        return {
            id: "option-blank",
            key: "",
            label: this.emptyOption,
            description: null,
            disabled: false,
            kind: "blank",
            object: null,
        };
    }

    protected get actionOption(): SearchSelectOption<T> | null {
        if (!this.actionLabel) return null;

        return {
            id: "option-action",
            key: "\u0000action",
            label: this.actionLabel,
            description: null,
            disabled: false,
            kind: "action",
            object: null,
        };
    }

    /**
     * Every option, in the order the keyboard moves through them.
     */
    protected get navigableOptions(): SearchSelectOption<T>[] {
        return [
            this.blankOption,
            ...this.optionGroups.flatMap((group) => group.options),
            this.actionOption,
        ].filter((option) => option !== null);
    }

    #activate(option: SearchSelectOption<T>): void {
        if (option.disabled) return;

        switch (option.kind) {
            case "action":
                this.hide();
                this.dispatchEvent(new SearchSelectActionEvent());

                return;
            case "blank":
                this.select(null);

                return;
            case "object":
                this.select(option.object);
        }
    }

    #moveActive(step: 1 | -1): void {
        const options = this.navigableOptions;

        if (!options.length) return;

        const currentIndex = options.findIndex((option) => option.key === this.activeKey);

        const nextIndex =
            currentIndex === -1
                ? step === 1
                    ? 0
                    : options.length - 1
                : torusIndex(options.length, currentIndex + step);

        this.activeKey = options[nextIndex].key;
    }

    //#endregion

    //#region Form value

    #syncFormValue(): void {
        this.internals.setFormValue(this.#value);

        if (this.#value) {
            this.internals.states.add("present");
        } else {
            this.internals.states.delete("present");
        }

        if (this.required && !this.#value) {
            this.internals.setValidity(
                { valueMissing: true },
                msg("This field is required."),
                this.anchor ?? undefined,
            );
        } else {
            this.internals.setValidity({});
        }
    }

    #stopEditing(): void {
        const hadQuery = !!this.query;

        this.editing = false;
        this.query = "";

        if (hadQuery) this.refresh();
    }

    /**
     * The accessible name of the input: `label`, else the text of the `<label>` elements
     * associated with this field, else the label of the enclosing horizontal form element.
     * Neither kind of label can reach the input inside the shadow root on its own.
     */
    protected get accessibleLabel(): string | null {
        if (this.label) return this.label;

        const text = Array.from(this.internals.labels, (label) => label.textContent?.trim() ?? "")
            .filter(Boolean)
            .join(" ");

        return text || this.closest("ak-form-element-horizontal")?.label || null;
    }

    /**
     * The text shown in the input: what the user is typing, else the selection's label.
     */
    protected get displayText(): string {
        if (this.editing) return this.query;

        if (this.selectedObject) return this.#labelOf(this.selectedObject);

        return this.value;
    }

    //#endregion

    //#region Positioning

    #startTracking(): void {
        if (!UsesAnchorFallback) return;

        const track = () => {
            const input = this.anchor;
            const listbox = this.listboxRef.value;

            if (input && listbox) {
                placeAnchoredPopover(input, listbox, { matchAnchorWidth: true });
            }

            this.#trackingFrame = requestAnimationFrame(track);
        };

        track();
    }

    #stopTracking(): void {
        if (this.#trackingFrame === null) return;

        cancelAnimationFrame(this.#trackingFrame);
        this.#trackingFrame = null;
    }

    //#endregion

    //#region Event Listeners

    @listen(AKRefreshEvent)
    protected refreshListener = () => {
        this.refresh();
    };

    #inputListener = (event: InputEvent) => {
        if (this.readOnly) return;

        const text = (event.target as HTMLInputElement).value;

        this.editing = true;
        this.query = text;
        this.activeKey = null;

        this.show();
        this.refresh();

        if (this.creatable) {
            this.selectedObject = null;
            this.value = text;
            this.dispatchEvent(new SearchSelectChangeEvent<T>(null));

            return;
        }

        if (!text && this.value) {
            this.selectedObject = null;
            this.value = "";
            this.dispatchEvent(new SearchSelectChangeEvent<T>(null));
        }
    };

    #keydownListener = (event: KeyboardEvent) => {
        if (this.readOnly) return;

        switch (event.key) {
            case "ArrowDown":
            case "ArrowUp": {
                event.preventDefault();

                if (!this.open) {
                    this.show();

                    return;
                }

                this.#moveActive(event.key === "ArrowDown" ? 1 : -1);

                return;
            }
            case "Enter": {
                if (!this.open) return;

                event.preventDefault();

                const active = this.navigableOptions.find(
                    (option) => option.key === this.activeKey,
                );

                if (active) {
                    this.#activate(active);
                } else {
                    this.#stopEditing();
                    this.hide();
                }

                return;
            }
            case "Escape": {
                if (!this.open && !this.editing) return;

                event.preventDefault();
                event.stopPropagation();

                this.#stopEditing();
                this.hide();

                return;
            }
            case "Tab":
                this.hide();

                return;
        }
    };

    #clickListener = () => {
        if (this.open) {
            this.hide();
        } else {
            this.show();
        }
    };

    #blurListener = () => {
        this.hide();

        if (this.editing && !this.creatable) {
            this.#stopEditing();
        } else {
            this.editing = false;
        }
    };

    #toggleListener = (event: ToggleEvent) => {
        if (event.newState === "open") {
            this.#startTracking();

            this.#openAbortController = new AbortController();

            this.ownerDocument.addEventListener("pointerdown", this.#outsidePointerDownListener, {
                capture: true,
                passive: true,
                signal: this.#openAbortController.signal,
            });
        } else {
            this.#stopTracking();
            this.#openAbortController?.abort();
            this.#openAbortController = null;
            this.activeKey = null;

            if (this.editing && !this.creatable) {
                this.#stopEditing();
            }
        }

        this.requestUpdate();
    };

    /**
     * Closes the listbox when the pointer goes down anywhere outside this element.
     */
    #outsidePointerDownListener = (event: PointerEvent) => {
        if (event.composedPath().includes(this)) return;

        this.hide();
    };

    /**
     * Keeps focus in the input while the pointer is on the listbox, so choosing an option
     * doesn't blur the input and close the popover first.
     */
    #listboxPointerDownListener = (event: PointerEvent) => {
        event.preventDefault();
    };

    //#endregion

    //#region Render

    protected renderOption(option: SearchSelectOption<T>): SlottedTemplateResult {
        const selected = option.kind !== "action" && option.key === this.value;
        const descriptionID = option.description ? `${option.id}-description` : null;

        return html`<div
            id=${option.id}
            role="option"
            class=${classMap({
                "ak-c-search-select__option": true,
                "ak-m-active": option.key === this.activeKey,
                "ak-m-action": option.kind === "action",
            })}
            aria-selected=${selected ? "true" : "false"}
            aria-disabled=${ifPresent(option.disabled ? "true" : null)}
            aria-describedby=${ifPresent(descriptionID)}
            @click=${() => this.#activate(option)}
        >
            <span class="ak-c-search-select__option-label">${option.label}</span>
            ${
                descriptionID
                    ? html`<span
                          id=${descriptionID}
                          class="ak-c-search-select__option-description"
                          aria-hidden="true"
                          >${option.description}</span
                      >`
                    : nothing
            }
        </div>`;
    }

    protected renderGroup(group: SearchSelectOptionGroup<T>, index: number): SlottedTemplateResult {
        if (!group.name) {
            return group.options.map((option) => this.renderOption(option));
        }

        const titleID = `group-${index}`;

        return html`<div role="group" aria-labelledby=${titleID}>
            <div id=${titleID} class="ak-c-search-select__group-title">${group.name}</div>
            ${group.options.map((option) => this.renderOption(option))}
        </div>`;
    }

    protected renderStatus(): SlottedTemplateResult {
        if (this.error) {
            return html`<div class="ak-c-search-select__status" role="alert">
                ${msg("Failed to fetch objects:")} ${pluckErrorDetail(this.error)}
            </div>`;
        }

        if (this.loading && !this.objects) {
            return html`<div class="ak-c-search-select__status">${msg("Loading...")}</div>`;
        }

        if (this.objects && !this.listedObjects.length) {
            return html`<div class="ak-c-search-select__status">${msg("No results found.")}</div>`;
        }

        return nothing;
    }

    protected override render(): SlottedTemplateResult {
        const { blankOption, actionOption } = this;
        const activeID = this.navigableOptions.find((option) => option.key === this.activeKey)?.id;

        return html`<input
                ${ref(this.anchorRef)}
                part="input"
                class="pf-c-form-control ak-c-search-select__input"
                type="text"
                role="combobox"
                autocomplete="off"
                spellcheck="false"
                aria-autocomplete="list"
                aria-controls="listbox"
                aria-expanded=${this.open ? "true" : "false"}
                aria-activedescendant=${ifPresent(activeID)}
                aria-busy=${this.loading ? "true" : "false"}
                aria-label=${ifPresent(this.accessibleLabel)}
                placeholder=${ifPresent(this.placeholder)}
                ?readonly=${this.readOnly}
                ?disabled=${this.disabled}
                ?required=${this.required}
                .value=${live(this.displayText)}
                @input=${this.#inputListener}
                @keydown=${this.#keydownListener}
                @click=${this.#clickListener}
                @blur=${this.#blurListener}
            />
            <div
                ${ref(this.listboxRef)}
                id="listbox"
                part="listbox"
                class="ak-c-search-select__listbox ak-m-thin-scrollbar"
                role="listbox"
                popover="manual"
                aria-label=${ifPresent(this.accessibleLabel)}
                @toggle=${this.#toggleListener}
                @pointerdown=${this.#listboxPointerDownListener}
            >
                ${blankOption ? this.renderOption(blankOption) : nothing}
                ${this.optionGroups.map((group, index) => this.renderGroup(group, index))}
                ${this.renderStatus()} ${actionOption ? this.renderOption(actionOption) : nothing}
            </div>`;
    }

    //#endregion
}

export default SearchSelect;

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select": SearchSelect;
    }
}
