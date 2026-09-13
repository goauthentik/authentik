import "../Progress";

import { akProgress, Progress, ProgressProps, ProgressSeverity, ProgressSize } from "../Progress";

import type { Meta, StoryObj } from "@storybook/web-components";

import { html } from "lit";

const meta: Meta<ProgressProps> = {
    title: "Components/Progress",
    component: "ak-progress",
    tags: ["autodocs"],
    parameters: {
        docs: {
            description: {
                component:
                    "A progress bar component that displays the completion progress of a task. Supports multiple variants, sizes, and severity states.",
            },
        },
    },
    argTypes: {
        variant: {
            control: { type: "select" },
            options: ["none", "top", "inside", "outside"],
            description: "Position of the progress value display",
        },
        size: {
            control: { type: "select" },
            options: ["sm", "lg"],
            description: "Size variant of the progress bar",
        },
        severity: {
            control: { type: "select" },
            options: ["success", "danger", "warning"],
            description: "Color theme indicating status severity",
        },
        min: {
            control: { type: "number" },
            description: "Minimum value",
        },
        max: {
            control: { type: "number" },
            description: "Maximum value",
        },
        value: {
            control: { type: "number" },
            description: "Current progress value",
        },
    },
    args: {
        variant: "top",
        min: 0,
        max: 100,
        value: 65,
    },
    decorators: [
        (story) =>
            html`<div>
                <style>
                    h4 {
                        font-weight: bold;
                        font-size: 1.25rem;
                        padding-bottom: 1.25rem;
                    }</style
                >${story()}
            </div>`,
    ],
};

export default meta;
type Story = StoryObj<Progress>;

// Basic progress bar
export const Default: Story = {
    parameters: {
        docs: {
            description: {
                story: "Default progress bar with top variant showing percentage completion.",
            },
        },
    },
};

// All variants comparison
export const Variants: Story = {
    parameters: {
        docs: {
            description: {
                story: "Comparison of all progress bar variants: none, top, inside, and outside.",
            },
        },
    },
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 2rem;">
            <div>
                <h4>None (no value display)</h4>
                <ak-progress variant="none" value="45"></ak-progress>
            </div>
            <div>
                <h4>Top (default)</h4>
                <ak-progress variant="top" value="65"
                    ><span slot="label">Loading data...</span></ak-progress
                >
            </div>
            <div>
                <h4>Inside</h4>
                <ak-progress variant="inside" value="80"
                    ><span slot="label">Processing files...</span></ak-progress
                >
            </div>
            <div>
                <h4>Outside</h4>
                <ak-progress variant="outside" value="30"
                    ><span slot="label">Uploading...</span></ak-progress
                >
            </div>
            <div>
                <h4>Indeterminate And Tiny</h4>
                <ak-progress variant="indeterminate" size="xs"></ak-progress>
            </div>
        </div>
    `,
};

// Severity states
export const SeverityStates: Story = {
    parameters: {
        docs: {
            description: {
                story: "Progress bars with different severity states",
            },
        },
    },
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 2rem;">
            <div>
                <h4>Success</h4>
                <ak-progress severity="success" value="100">
                    <label slot="label">Operation completed</label>
                </ak-progress>
            </div>
            <div>
                <h4>Warning</h4>
                <ak-progress severity="warning" value="75">
                    <label slot="label">Some issues detected</label>
                </ak-progress>
            </div>
            <div>
                <h4>Danger</h4>
                <ak-progress severity="danger" value="25">
                    <label slot="label">Critical errors found</label>
                </ak-progress>
            </div>
        </div>
    `,
};

// Size variants
export const Sizes: Story = {
    parameters: {
        docs: {
            description: {
                story: "Progress bars in different sizes: small, default, and large.",
            },
        },
    },
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 2rem;">
            <div>
                <h4>Small</h4>
                <ak-progress size="sm" value="60"
                    ><span slot="label">Compact progress</span></ak-progress
                >
            </div>
            <div>
                <h4>Default</h4>
                <ak-progress value="60"><span slot="label">Standard progress</span></ak-progress>
            </div>
            <div>
                <h4>Large</h4>
                <ak-progress size="lg" value="60"
                    ><span slot="label">Prominent progress</span></ak-progress
                >
            </div>
        </div>
    `,
};

// Custom value display
export const CustomValueDisplay: Story = {
    parameters: {
        docs: {
            description: {
                story: "Progress bar with custom value formatting function.",
            },
        },
    },
    args: {
        value: 45,
        max: 200,
        displayValue: (value: number) => `${value} of 200 items`,
    },
    render: (args) => html`
        <ak-progress .value=${args.value} .max=${args.max} .displayValue=${args.displayValue}>
            <label slot="label">Processing items...</label>
        </ak-progress>
    `,
};

// Custom range
export const CustomRange: Story = {
    parameters: {
        docs: {
            description: {
                story: "Progress bar with custom min/max range and value display.",
            },
        },
    },
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 2rem;">
            <div>
                <h4>Temperature range (°F)</h4>
                <ak-progress
                    min="32"
                    max="212"
                    value="72"
                    .displayValue=${(value: number) => `${value}°F`}
                >
                    <span slot="label">Current temperature (between freezing and boiling)</span>
                </ak-progress>
            </div>
            <div>
                <h4>Score range</h4>
                <ak-progress
                    min="0"
                    max="500"
                    value="350"
                    .displayValue=${(value: number) => `${value}/500 points`}
                >
                    <span slot="label">Quiz score</span>
                </ak-progress>
            </div>
        </div>
    `,
};

// Animation simulation
export const AnimatedProgress: Story = {
    parameters: {
        docs: {
            description: {
                story: "Simulated animated progress bar (updates every second).",
            },
        },
    },
    render: () => {
        let progress = 0;
        const updateProgress = () => {
            const progressBar = document.querySelector("#animated-progress") as Progress;
            if (progressBar) {
                progress = (progress + 5) % 105;
                progressBar.value = progress;
                if (progress >= 100) {
                    progressBar.severity = "success";
                } else {
                    progressBar.severity = undefined;
                }
            }
        };

        // Start animation on story load
        setTimeout(() => {
            const interval = setInterval(updateProgress, 500);
            // Clean up after 30 seconds
            setTimeout(() => clearInterval(interval), 30000);
        }, 100);

        return html`
            <ak-progress id="animated-progress" value="0">
                <label slot="label">Processing... </label></ak-progress
            >
        `;
    },
};

// Edge cases
export const EdgeCases: Story = {
    parameters: {
        docs: {
            description: {
                story: "Edge cases: zero progress, complete progress, over-maximum and under-minimum values.  The <code>value</code> property is clamped at render, but will reflect whatever the user has set internally (although see the <code>one way</code> demo for caveats). ",
            },
        },
    },
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 2rem;">
            <div>
                <h4>Zero progress</h4>
                <ak-progress value="0"><label slot="label">Not started</label></ak-progress>
            </div>
            <div>
                <h4>Complete</h4>
                <ak-progress value="100" severity="success"
                    ><label slot="label"> Completed</label>
                </ak-progress>
            </div>
            <div>
                <h4>Over maximum (should clamp to 100%)</h4>
                <ak-progress value="150"><label slot="label">Overflow test</label></ak-progress>
            </div>
            <div>
                <h4>Negative value (should show as 0%)</h4>
                <ak-progress value="-10"><label slot="label">Underflow test</label></ak-progress>
            </div>
        </div>
    `,
};

// Complex layout combinations
export const ComplexLayouts: Story = {
    parameters: {
        docs: {
            description: {
                story: "Showing off a bit of mix-and-match of attributes and settings.",
            },
        },
    },
    render: () => html`
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <h4>Small + Inside + Warning</h4>
                <ak-progress size="sm" variant="inside" severity="warning" value="45">
                    <span slot="label">Compact warning</span>
                </ak-progress>
            </div>
            <div>
                <h4>Large + Outside + Success</h4>
                <ak-progress size="lg" variant="outside" severity="success" value="90">
                    <span slot="label">Large success indicator</span>
                </ak-progress>
            </div>
            <div>
                <h4>Default + None + Danger</h4>
                <ak-progress variant="none" severity="danger" value="15">
                    <span slot="label">Silent danger</span>
                </ak-progress>
            </div>
            <div>
                <h4>Small + Top + Custom Value</h4>
                <ak-progress
                    size="sm"
                    variant="top"
                    value="33"
                    .displayValue=${(v: number) => `Step ${Math.floor(v / 10) + 1}/10`}
                >
                    <span slot="label">Step progress</span>
                </ak-progress>
            </div>
        </div>
    `,
};

export const InteractiveControls: Story = {
    parameters: {
        docs: {
            description: {
                story: "Demo for the <code>one-way</code> attribute, which prevents the progress meter from going backwards. In some cases, going backward might be... alarming. 😁",
            },
        },
    },
    render: () => {
        const handleIncrement = (id: string) => {
            const progress = document.querySelector(`#${id}`) as Progress;
            if (progress) {
                progress.value = Math.min(progress.value + 5, progress.max);
            }
        };

        const handleDecrement = (id: string) => {
            const progress = document.querySelector(`#${id}`) as Progress;
            if (progress) {
                progress.value = Math.max(progress.value - 5, progress.min);
            }
        };

        const handleReset = (id: string) => {
            const progress = document.querySelector(`#${id}`) as Progress;
            if (progress) {
                progress.reset();
            }
        };

        return html`
            <div style="display: flex; flex-direction: column; gap: 3rem;">
                <div>
                    <h4>Normal Progress (bidirectional)</h4>
                    <ak-progress id="normal-progress" value="50">
                        <span slot="label">Normal progress control</span>
                    </ak-progress>
                    <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                        <button type="button" @click=${() => handleIncrement("normal-progress")}>
                            Increment (+5%)
                        </button>
                        <button type="button" @click=${() => handleDecrement("normal-progress")}>
                            Decrement (-5%)
                        </button>
                        <button type="button" @click=${() => handleReset("normal-progress")}>
                            Reset
                        </button>
                    </div>
                </div>

                <div>
                    <h4>One-Way Progress (prevents decreases)</h4>
                    <ak-progress id="oneway-progress" value="50" one-way>
                        <span slot="label">One-way progress control</span>
                    </ak-progress>
                    <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                        <button type="button" @click=${() => handleIncrement("oneway-progress")}>
                            Increment (+5%)
                        </button>
                        <button
                            type="button"
                            @click=${() => handleDecrement("oneway-progress")}
                            style="opacity: 0.6;"
                            title="This will set the value property but won't change the display"
                        >
                            Decrement (-5%)
                        </button>
                        <button type="button" @click=${() => handleReset("oneway-progress")}>
                            Reset
                        </button>
                    </div>
                    <p style="font-size: 0.875rem; color: #666; margin-top: 0.5rem;">
                        <em
                            >Note: The decrement button will modify the HTML attribute but the
                            visual progress won't decrease due to one-way protection.</em
                        >
                    </p>
                </div>
            </div>
        `;
    },
};

export const BuilderBasic: Story = {
    parameters: {
        docs: {
            description: {
                story: "Using the akProgress builder function for programmatic progress bar creation.",
            },
        },
    },
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 2rem;">
            ${akProgress({
                value: 45,
                label: "File upload progress",
            })}
            ${akProgress({
                variant: "inside",
                value: 75,
                severity: "warning",
                label: "Validation warnings detected",
            })}
            ${akProgress({
                variant: "outside",
                value: 100,
                severity: "success",
                label: html`<strong>Migration completed successfully!</strong>`,
            })}
        </div>
    `,
};

// Builder with dynamic content generation
export const BuilderDynamic: Story = {
    parameters: {
        docs: {
            description: {
                story: "Demonstrating dynamic progress bar generation using the builder function.",
            },
        },
    },
    render: () => {
        const tasks = [
            { name: "Database backup", progress: 100, status: "success" },
            { name: "File migration", progress: 67, status: "warning" },
            { name: "Index rebuild", progress: 23, status: undefined },
            { name: "Cache cleanup", progress: 0, status: undefined },
        ];

        return html`
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <h4>System Maintenance Tasks</h4>
                ${tasks.map((task) =>
                    akProgress({
                        value: task.progress,
                        severity: task.status as ProgressSeverity,
                        variant: "top",
                        label: html`
                            <div
                                style="display: flex; justify-content: space-between; align-items: center;"
                            >
                                <span>${task.name}</span>
                                <small style="opacity: 0.7;">
                                    ${task.progress === 0
                                        ? "Pending"
                                        : task.progress === 100
                                          ? "Complete"
                                          : "In Progress"}
                                </small>
                            </div>
                        `,
                    }),
                )}
            </div>
        `;
    },
};

// Builder with custom formatting
export const BuilderCustomFormatting: Story = {
    parameters: {
        docs: {
            description: {
                story: "Builder function with custom value display formatting and ranges.",
            },
        },
    },
    render: () => html`
        <div style="display: flex; flex-direction: column; gap: 2rem;">
            ${akProgress({
                min: 0,
                max: 500,
                value: 387,
                displayValue: (value: number) => `${value} MB / 500 MB`,
                label: "Memory usage",
                severity: "warning",
            })}
            ${akProgress({
                min: -10,
                max: 40,
                value: 23,
                displayValue: (value: number) => `${value}°C`,
                variant: "inside",
                label: "CPU Temperature",
            })}
            ${akProgress({
                min: 0,
                max: 1000,
                value: 847,
                displayValue: (value: number) => {
                    if (value < 100) return `${value} items`;
                    if (value < 1000) return `${(value / 100).toFixed(1)}K items`;
                    return `${(value / 1000).toFixed(1)}M items`;
                },
                variant: "outside",
                label: "Items processed",
            })}
        </div>
    `,
};

// Builder reactive updates
export const BuilderReactive: Story = {
    parameters: {
        docs: {
            description: {
                story: "Demonstrating reactive updates with the builder function and one-way progress.",
            },
        },
    },
    render: () => {
        let normalProgress = 30;
        let oneWayProgress = 30;

        const updateProgress = () => {
            const container = document.querySelector("#reactive-container");
            if (!container) return;

            // Simulate fluctuating normal progress
            normalProgress = Math.max(
                0,
                Math.min(100, normalProgress + (Math.random() - 0.5) * 20),
            );

            // Simulate only increasing one-way progress
            oneWayProgress = Math.min(100, oneWayProgress + Math.random() * 5);

            const normalEl = container.querySelector("#normal-reactive");
            const oneWayEl = container.querySelector("#oneway-reactive");

            if (normalEl) {
                (normalEl as Progress).value = normalProgress;
            }
            if (oneWayEl) {
                (oneWayEl as Progress).value = oneWayProgress;
            }

            // Update severity based on progress
            if (normalEl) {
                (normalEl as Progress).severity =
                    normalProgress > 80
                        ? "success"
                        : normalProgress < 30
                          ? "danger"
                          : normalProgress < 60
                            ? "warning"
                            : undefined;
            }
        };

        // Start updates after render
        setTimeout(() => {
            const interval = setInterval(updateProgress, 1000);
            setTimeout(() => clearInterval(interval), 15000);
        }, 100);

        return html`
            <div id="reactive-container" style="display: flex; flex-direction: column; gap: 2rem;">
                <div>
                    <h4>Reactive Normal Progress</h4>
                    ${akProgress({
                        value: normalProgress,
                        variant: "top",
                        label: "Fluctuating system metric",
                    })}
                </div>

                <div>
                    <h4>Reactive One-Way Progress</h4>
                    ${akProgress({
                        value: oneWayProgress,
                        variant: "inside",
                        oneWay: true,
                        label: "Download progress (one-way)",
                    })}
                </div>

                <p style="font-size: 0.875rem; color: #666;">
                    <em>These progress bars update automatically every second for 15 seconds.</em>
                </p>
            </div>
        `;
    },
};

// Builder composition patterns
export const BuilderComposition: Story = {
    parameters: {
        docs: {
            description: {
                story: "Advanced composition patterns using the builder function in different layouts.",
            },
        },
    },
    render: () => html`
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <h4>Dashboard Card Style</h4>
                <div
                    style="border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; background: #f9f9f9;"
                >
                    ${akProgress({
                        variant: "none",
                        value: 73,
                        label: html`
                            <div
                                style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;"
                            >
                                <span style="font-weight: 500;">Server Load</span>
                                <span style="font-size: 0.875rem; color: #666;">73%</span>
                            </div>
                        `,
                    })}
                    <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #888;">
                        Last updated: 2 minutes ago
                    </div>
                </div>
            </div>

            <div>
                <h4>Inline Status Style</h4>
                <div style="border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem;">
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        ${akProgress({
                            variant: "outside",
                            value: 100,
                            severity: "success",
                            size: "sm" as ProgressSize,
                            label: "Backup completed",
                        })}
                        ${akProgress({
                            variant: "outside",
                            value: 67,
                            severity: "warning",
                            size: "sm" as ProgressSize,
                            label: "Sync in progress",
                        })}
                        ${akProgress({
                            variant: "outside",
                            value: 0,
                            size: "sm",
                            label: "Pending cleanup",
                        })}
                    </div>
                </div>
            </div>
        </div>
    `,
};
