/**
 * @file The result shape every tool and make wrapper returns.
 *   `skipped` means the check chose not to look at something. `unknown` means it tried and couldn't
 *   tell. The summary names both, so an agent repeating it verbatim stays accurate.
 */

export interface Item {
    what: string;
    reason: string;
}

export interface ResultData {
    tool: string;
    ok: boolean;
    summary: string;
    checked: string[];
    skipped: Item[];
    unknown: Item[];
    commands: string[];
    fingerprint: string | null;
    data: Record<string, unknown>;
}

export class Result implements ResultData {
    public tool: string;
    public ok = true;
    public summary = "";
    public checked: string[] = [];
    public skipped: Item[] = [];
    public unknown: Item[] = [];
    public commands: string[] = [];
    public fingerprint: string | null = null;
    public data: Record<string, unknown> = {};

    constructor(tool: string) {
        this.tool = tool;
    }

    public skip(what: string, reason: string): void {
        this.skipped.push({ what, reason });
    }

    public unsure(what: string, reason: string): void {
        this.unknown.push({ what, reason });
    }

    public fail(): void {
        this.ok = false;
    }

    public command(cmd: string): void {
        if (!this.commands.includes(cmd)) this.commands.push(cmd);
    }

    /** Set the summary from a headline plus the skipped and unknown items. */
    public finish(headline: string): this {
        const parts = [`${headline.replace(/\.$/, "")}.`];
        const list = (items: Item[]) => items.map((i) => `${i.what} (${i.reason})`).join("; ");

        if (this.skipped.length) parts.push(`Skipped: ${list(this.skipped)}.`);

        if (this.unknown.length) parts.push(`Unknown: ${list(this.unknown)}.`);
        this.summary = parts.join(" ");

        return this;
    }

    public toJSON(): ResultData {
        return {
            tool: this.tool,
            ok: this.ok,
            summary: this.summary,
            checked: this.checked,
            skipped: this.skipped,
            unknown: this.unknown,
            commands: this.commands,
            fingerprint: this.fingerprint,
            data: this.data,
        };
    }

    /** A human summary for terminals and clients without structured output. */
    public toText(): string {
        const lines = [`${this.ok ? "OK" : "FAIL"} [${this.tool}] ${this.summary}`];

        for (const i of this.skipped) lines.push(`  skipped: ${i.what}: ${i.reason}`);

        for (const i of this.unknown) lines.push(`  unknown: ${i.what}: ${i.reason}`);

        for (const c of this.commands) lines.push(`  run: ${c}`);

        return lines.join("\n");
    }
}
