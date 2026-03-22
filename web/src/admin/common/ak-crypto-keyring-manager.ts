import "#elements/EmptyState";
import "#elements/forms/ModalForm";
import "#admin/common/ak-crypto-keyring-binding-form";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import type { BindingDraft } from "#admin/common/ak-crypto-keyring-binding-form";

import { CertificateKeyPairRing, CryptoApi, KeyTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

export type BindingRow = {
    order: number;
    keypair: string;
    keypairName?: string;
    fingerprintSha256?: string;
    privateKeyAvailable?: boolean;
};

type RingBindingDTO = {
    uuid?: string;
    order?: number;
    keypair?: string;
    keypairName?: string;
    fingerprintSha256?: string;
    privateKeyAvailable?: boolean;
};

function getRingBindings(ring: unknown): RingBindingDTO[] {
    if (!ring || typeof ring !== "object") return [];
    const maybe = (ring as Record<string, unknown>).bindings;
    return Array.isArray(maybe) ? (maybe as RingBindingDTO[]) : [];
}

@customElement("ak-crypto-keyring-manager")
export class AkCryptoKeyringManager extends Table<BindingRow> {
    @property({ type: String, attribute: "ring-uuid" })
    ringUuid?: string;

    @property({ type: Boolean, attribute: "require-key" })
    requireKey = false;

    @property({ type: Array, attribute: "allowed-key-types" })
    allowedKeyTypes?: KeyTypeEnum[];

    @state()
    private ring?: CertificateKeyPairRing;

    @state()
    private rowsLocal: BindingRow[] = [];

    @state()
    private saving = false;

    @state()
    private loadingRing = false;

    @state()
    private errorMessage?: string;

    @state()
    private hasLoaded = false;

    checkbox = true;
    // clearOnRefresh は “ローカル state が真” の Table では不要寄り。残したければ true のままでもOK
    clearOnRefresh = false;
    order = "order";

    protected columns: TableColumn[] = [
        [msg("Order"), "order"],
        [msg("Keypair")],
        [msg("Fingerprint (SHA256)")],
        [msg("Private key")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    connectedCallback(): void {
        super.connectedCallback();
        this.loadRing().catch(() => undefined);
    }

    override willUpdate(changed: PropertyValues<this>): void {
        super.willUpdate(changed);

        if (changed.has("ringUuid")) {
            if (this.ringUuid) {
                this.loadRing().catch(() => undefined);
            } else {
                this.setRows([]);
                this.ring = undefined;
                this.hasLoaded = true;
            }
        }
    }

    async apiEndpoint(): Promise<PaginatedResponse<BindingRow>> {
        return {
            pagination: {
                count: this.rowsLocal.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: this.rowsLocal.length,
                next: 0,
                previous: 0,
            },
            results: [...this.rowsLocal].sort((a, b) => a.order - b.order),
        };
    }

    protected override rowLabel(item: BindingRow): string {
        return `#${item.order} ${item.keypairName ?? item.keypair}`;
    }

    private setRows(next: BindingRow[]) {
        const sorted = [...next].sort((a, b) => a.order - b.order);
        this.rowsLocal = sorted.map((r, i) => ({ ...r, order: i }));
        this.errorMessage = undefined;
        this.fetch().catch(() => undefined);
    }

    private get excludedKeypairPks(): string[] {
        return this.rowsLocal.map((r) => String(r.keypair));
    }

    private applyDraft(draft: BindingDraft, existingKeypair?: string): void {
        const keypair = draft.keypair;
        const order = Number(draft.order ?? 0);

        if (!keypair) {
            this.errorMessage = msg("Please select a keypair.");
            return;
        }
        if (!Number.isFinite(order) || order < 0) {
            this.errorMessage = msg("Order must be a number >= 0.");
            return;
        }

        const dup = this.rowsLocal.some(
            (r) => r.keypair === keypair && r.keypair !== existingKeypair,
        );
        if (dup) {
            this.errorMessage = msg("This keypair is already in the ring.");
            return;
        }

        if (existingKeypair) {
            this.setRows(
                this.rowsLocal.map((r) =>
                    r.keypair === existingKeypair ? { ...r, keypair, order } : r,
                ),
            );
            return;
        }

        this.setRows([...this.rowsLocal, { order, keypair }]);
    }

    private async loadRing(): Promise<void> {
        this.errorMessage = undefined;
        if (!this.ringUuid) return;

        this.loadingRing = true;
        try {
            const ring = await new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairringsRetrieve({
                ringUuid: this.ringUuid,
            });
            this.ring = ring;

            const raw = getRingBindings(ring);
            const rows: BindingRow[] = raw.map((b) => ({
                order: Number(b.order ?? 0),
                keypair: String(b.keypair),
                keypairName: b.keypairName,
                fingerprintSha256: b.fingerprintSha256,
                privateKeyAvailable: !!b.privateKeyAvailable,
            }));
            this.setRows(rows);
        } catch (e: unknown) {
            this.errorMessage = e instanceof Error ? e.message : String(e);
        } finally {
            this.loadingRing = false;
            this.hasLoaded = true;
        }
    }

    public async persist(): Promise<void> {
        if (!this.ringUuid) return;

        this.saving = true;
        this.errorMessage = undefined;
        try {
            await new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairringsSetBindingsUpdate({
                ringUuid: this.ringUuid,
                certificateKeyPairRingBindingsReplaceRequest: {
                    bindings: [...this.rowsLocal]
                        .sort((a, b) => a.order - b.order)
                        .map((r) => ({ order: r.order, keypair: r.keypair })),
                },
            });

            await this.loadRing();
            this.dispatchEvent(new CustomEvent("ak-ring-saved", { bubbles: true, composed: true }));
        } catch (e: unknown) {
            this.errorMessage = e instanceof Error ? e.message : String(e);
        } finally {
            this.saving = false;
        }
    }

    private renderErrorBox(): TemplateResult {
        return this.errorMessage
            ? html`<div class="pf-c-alert pf-m-danger" aria-label="error">
                  <div class="pf-c-alert__title">${msg("Error")}</div>
                  <div class="pf-c-alert__description"><pre>${this.errorMessage}</pre></div>
              </div>`
            : html``;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`
            <button
                class="pf-c-button pf-m-danger"
                type="button"
                ?disabled=${disabled}
                @click=${() => {
                    const selected = new Set(this.selectedElements.map((e) => e.keypair));
                    this.setRows(this.rowsLocal.filter((r) => !selected.has(r.keypair)));
                }}
            >
                ${msg("Delete")}
            </button>
        `;
    }

    renderToolbar(): TemplateResult {
        const exclude = this.excludedKeypairPks;

        return html`
            <ak-forms-modal size=${PFSize.Medium}>
                <span slot="header">${msg("Add keypair to ring")}</span>

                <ak-crypto-keyring-binding-form
                    slot="form"
                    .order=${this.rowsLocal.length}
                    .keypair=${null}
                    ?require-key=${this.requireKey}
                    .allowedKeyTypes=${this.allowedKeyTypes ?? []}
                    .excludeKeypairs=${exclude}
                ></ak-crypto-keyring-binding-form>

                <button slot="trigger" class="pf-c-button pf-m-primary" type="button">
                    ${msg("Add key")}
                </button>

                <button
                    slot="submit"
                    class="pf-c-button pf-m-primary"
                    type="button"
                    @click=${(ev: Event) => {
                        ev.preventDefault();
                        ev.stopPropagation();

                        const modal = (ev.currentTarget as HTMLElement).closest("ak-forms-modal");
                        const form = modal?.querySelector("ak-crypto-keyring-binding-form") as {
                            buildDraft?: () => BindingDraft | undefined;
                        } | null;

                        const draft = form?.buildDraft?.();
                        if (!draft) return;

                        this.applyDraft(draft);
                        modal?.dispatchEvent(new CustomEvent("ak-close", { bubbles: true }));
                    }}
                >
                    ${msg("Add")}
                </button>
            </ak-forms-modal>

            ${super.renderToolbar()}
        `;
    }

    row(item: BindingRow): SlottedTemplateResult[] {
        const exclude = this.excludedKeypairPks.filter((pk) => pk !== item.keypair);

        return [
            html`<pre>${item.order}</pre>`,
            html`${item.keypairName ?? item.keypair}`,
            html`<code>${item.fingerprintSha256 ?? ""}</code>`,
            html`${item.privateKeyAvailable ? msg("Yes") : msg("No")}`,
            html`
                <ak-forms-modal size=${PFSize.Medium}>
                    <span slot="header">${msg("Edit ring binding")}</span>

                    <ak-crypto-keyring-binding-form
                        slot="form"
                        .order=${item.order}
                        .keypair=${item.keypair}
                        ?require-key=${this.requireKey}
                        .allowedKeyTypes=${this.allowedKeyTypes ?? []}
                        .excludeKeypairs=${exclude}
                    ></ak-crypto-keyring-binding-form>

                    <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                        ${msg("Edit")}
                    </button>

                    <button
                        slot="submit"
                        class="pf-c-button pf-m-primary"
                        type="button"
                        @click=${(ev: Event) => {
                            ev.preventDefault();
                            ev.stopPropagation();

                            const modal = (ev.currentTarget as HTMLElement).closest(
                                "ak-forms-modal",
                            );
                            const form = modal?.querySelector("ak-crypto-keyring-binding-form") as {
                                buildDraft?: () => BindingDraft | undefined;
                            } | null;

                            const draft = form?.buildDraft?.();
                            if (!draft) return;

                            this.applyDraft(draft, item.keypair);
                            modal?.dispatchEvent(new CustomEvent("ak-close", { bubbles: true }));
                        }}
                    >
                        ${msg("Update")}
                    </button>
                </ak-forms-modal>
            `,
        ];
    }

    override render(): TemplateResult {
        if (!this.ringUuid) {
            return html`<p class="pf-c-form__helper-text">${msg("No ring selected.")}</p>`;
        }
        if (!this.hasLoaded || this.loadingRing) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        return html`
            <div class="pf-c-content">
                <h3>${msg("Key ring")}${this.ring?.name ? html`: ${this.ring.name}` : nothing}</h3>
                ${this.renderErrorBox()} ${super.render()}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-crypto-keyring-manager": AkCryptoKeyringManager;
    }
}
