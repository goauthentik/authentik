import { type DriveEntry, type DriveState, emptyDriveState, parentPath } from "./file-browser";
import Styles from "./file-sidebar.css";
import type { TransferStatus } from "./file-transfer";
import PFButton from "@patternfly/patternfly/components/Button/button.css";

import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

export function fileSize(size?: number): string {
    if (size === undefined) return msg("Unknown", { id: "rac.files.size.unknown.label" });

    if (size < 1024) return `${size} B`;
    const unit = Math.min(Math.floor(Math.log(size) / Math.log(1024)), 4);

    return `${(size / 1024 ** unit).toLocaleString(undefined, { maximumFractionDigits: 1 })} ${["B", "KiB", "MiB", "GiB", "TiB"][unit]}`;
}

@customElement("ak-rac-file-sidebar")
export class FileSidebar extends AKElement {
    static styles = [...(super.styles ?? []), PFButton, Styles];

    @property({ attribute: false }) drive: DriveState = emptyDriveState();
    @property({ attribute: false }) transfers: TransferStatus[] = [];
    @property({ type: Boolean }) disabled = false;

    private action(type: string, detail: unknown = {}): void {
        this.dispatchEvent(
            new CustomEvent(`rac-files-${type}`, { detail, bubbles: true, composed: true }),
        );
    }

    private entry(entry: DriveEntry) {
        return html`<tr>
            <td class="entry-name" title=${entry.name}>
                <i
                    class=${entry.directory ? "fas fa-folder" : "fas fa-file"}
                    aria-hidden="true"
                ></i>
                ${
                    entry.directory
                        ? html`<button
                              class="pf-c-button pf-m-link directory-link"
                              @click=${() => this.action("navigate", { path: entry.path })}
                          >
                              ${entry.name}
                          </button>`
                        : html`<span>${entry.name}</span>`
                }
            </td>
            <td>
                ${
                    entry.directory
                        ? msg("Folder", { id: "rac.files.type.directory.label" })
                        : msg("File", { id: "rac.files.type.file.label" })
                }
            </td>
            <td class="entry-size">${entry.directory ? "—" : fileSize(entry.size)}</td>
            <td>
                ${
                    entry.directory
                        ? nothing
                        : html`<button
                              class="pf-c-button pf-m-plain"
                              ?disabled=${this.disabled}
                              title=${msg("Download", { id: "rac.files.download.label" })}
                              aria-label=${`${msg("Download", { id: "rac.files.download.label" })}: ${entry.name}`}
                              @click=${() => this.action("download", { entry })}
                          >
                              <i class="fas fa-download" aria-hidden="true"></i>
                          </button>`
                }
            </td>
        </tr>`;
    }

    private transfer(status: TransferStatus) {
        const label =
            status.phase === "error"
                ? msg("File transfer failed", { id: "rac.transfer.status.error" })
                : status.phase === "complete"
                  ? status.direction === "download"
                      ? msg("Transferred to browser", { id: "rac.transfer.download.success" })
                      : msg("Upload complete", { id: "rac.transfer.upload.success" })
                  : status.direction === "upload"
                    ? msg("Uploading", { id: "rac.transfer.upload.description" })
                    : msg("Downloading", { id: "rac.transfer.download.description" });

        const percent =
            status.total === undefined
                ? undefined
                : status.total === 0
                  ? 100
                  : Math.min(100, Math.floor((status.transferred / status.total) * 100));

        return html`<li class="transfer-item" data-phase=${status.phase}>
            <div class="transfer-heading">
                <span title=${status.path || status.name}>${status.name}</span>
                <button
                    class="pf-c-button pf-m-plain"
                    @click=${() =>
                        this.action(status.phase === "active" ? "cancel" : "dismiss", {
                            id: status.id,
                        })}
                    aria-label=${`${status.phase === "active" ? msg("Cancel", { id: "rac.transfer.cancel.label" }) : msg("Dismiss", { id: "rac.transfer.dismiss.label" })}: ${status.name}`}
                >
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
            </div>
            <span class="transfer-phase" role="status">${label}</span>
            ${
                status.phase === "active"
                    ? percent === undefined
                        ? html`<progress aria-label=${status.name}></progress>`
                        : html`<progress
                              value=${percent}
                              max="100"
                              aria-label=${status.name}
                          ></progress>`
                    : nothing
            }
            <small
                >${fileSize(status.transferred)}${
                    status.total !== undefined ? ` / ${fileSize(status.total)} (${percent}%)` : ""
                }</small
            >
            ${status.error ? html`<span class="error">${status.error}</span>` : nothing}
            ${
                status.queuedNames?.length && status.phase === "active"
                    ? html`<div class="queued">
                          <span>${msg("Queued files", { id: "rac.transfer.queue.label" })}</span>
                          <ul>
                              ${status.queuedNames.map((name) => html`<li>${name}</li>`)}
                          </ul>
                      </div>`
                    : nothing
            }
        </li>`;
    }

    render() {
        const noDrive = !this.drive.ready;

        return html`<section
            aria-label=${msg("Files", { id: "rac.files.title.label" })}
            @keydown=${(event: KeyboardEvent) => {
                event.stopPropagation();

                if (event.key === "Escape") {
                    event.preventDefault();
                    this.action("close");
                }
            }}
            @keyup=${(event: KeyboardEvent) => event.stopPropagation()}
        >
            <header>
                <h2>${msg("Files", { id: "rac.files.title.label" })}</h2>
                <button
                    class="pf-c-button pf-m-plain"
                    aria-label=${msg("Close files", { id: "rac.files.close.aria-label" })}
                    @click=${() => this.action("close")}
                >
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
            </header>
            <nav aria-label=${msg("Current directory", { id: "rac.files.directory.aria-label" })}>
                <button
                    class="pf-c-button pf-m-plain"
                    ?disabled=${noDrive || this.drive.path === "/"}
                    aria-label=${msg("Parent directory", { id: "rac.files.parent.aria-label" })}
                    @click=${() => this.action("navigate", { path: parentPath(this.drive.path) })}
                >
                    <i class="fas fa-arrow-up" aria-hidden="true"></i>
                </button>
                <span class="current-path" title=${this.drive.path}>${this.drive.path}</span>
                <button
                    class="pf-c-button pf-m-plain"
                    ?disabled=${noDrive || this.disabled || this.drive.loading}
                    aria-label=${msg("Refresh files", { id: "rac.files.refresh.aria-label" })}
                    @click=${() => this.action("navigate", { path: this.drive.path })}
                >
                    <i class="fas fa-sync-alt" aria-hidden="true"></i>
                </button>
            </nav>
            <div class="upload-action">
                <button
                    class="pf-c-button pf-m-primary"
                    ?disabled=${
                        noDrive || this.disabled || this.drive.loading || !!this.drive.error
                    }
                    @click=${() =>
                        this.renderRoot
                            .querySelector<HTMLInputElement>("input[type=file]")
                            ?.click()}
                >
                    <i class="fas fa-upload" aria-hidden="true"></i> ${msg("Upload files", {
                        id: "rac.transfer.upload.label",
                    })}
                </button>
                <input
                    type="file"
                    multiple
                    hidden
                    tabindex="-1"
                    @change=${(event: Event) => {
                        const input = event.target as HTMLInputElement;
                        this.action("upload", { files: Array.from(input.files || []) });
                        input.value = "";
                    }}
                />
            </div>
            <div class="file-list" aria-busy=${this.drive.loading}>
                ${
                    this.drive.error
                        ? html`<p class="error" role="alert">${this.drive.error}</p>`
                        : nothing
                }
                ${
                    noDrive
                        ? html`<p class="empty-state">
                              ${msg("No virtual drive is available for this connection.", {
                                  id: "rac.files.drive.empty.description",
                              })}
                          </p>`
                        : this.drive.loading
                          ? html`<p class="empty-state" role="status">
                                ${msg("Loading files…", { id: "rac.files.loading.description" })}
                            </p>`
                          : !this.drive.entries.length && !this.drive.error
                            ? html`<p class="empty-state">
                                  ${msg("This directory is empty.", {
                                      id: "rac.files.empty.description",
                                  })}
                              </p>`
                            : html`<table>
                                  <thead>
                                      <tr>
                                          <th>${msg("Name", { id: "rac.files.name.label" })}</th>
                                          <th>${msg("Type", { id: "rac.files.type.label" })}</th>
                                          <th>${msg("Size", { id: "rac.files.size.label" })}</th>
                                          <th>
                                              <span class="pf-u-screen-reader"
                                                  >${msg("Actions", {
                                                      id: "rac.files.actions.label",
                                                  })}</span
                                              >
                                          </th>
                                      </tr>
                                  </thead>
                                  <tbody>
                                      ${this.drive.entries.map((entry) => this.entry(entry))}
                                  </tbody>
                              </table>`
                }
            </div>
            ${
                this.transfers.length
                    ? html`<section
                          class="transfers"
                          aria-label=${msg("Transfers", { id: "rac.files.transfers.label" })}
                      >
                          <h3>${msg("Transfers", { id: "rac.files.transfers.label" })}</h3>
                          <ul>
                              ${this.transfers.map((status) => this.transfer(status))}
                          </ul>
                      </section>`
                    : nothing
            }
        </section>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rac-file-sidebar": FileSidebar;
    }
}
