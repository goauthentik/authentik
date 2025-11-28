/**
 * @file Wave animation module.
 */

/**
 * Data offsets (11 properties per particle)
 */
const ParticleOffsets = {
    BASE_X: 0,
    BASE_Z: 1,
    BASE_Y: 2,
    R: 3,
    G: 4,
    B: 5,
    A: 6,
    SIZE: 7,
    PERSPECTIVE_SIZE: 8,
    HALF_SIZE: 9,
    PERSPECTIVE_DEPTH_ALPHA: 10,
    PARTICLE_SIZE: 11,
};

/**
 * @typedef {object} Particle
 * @property {number} baseX
 * @property {number} baseZ
 * @property {number} baseY
 * @property {number} x
 * @property {number} y
 * @property {number} r
 * @property {number} g
 * @property {number} b
 * @property {number} a
 * @property {number} size
 * @property {number} perspectiveSize
 * @property {number} halfSize
 * @property {number} perspectiveDepthAlpha
 */
export class WavesCanvas {
    //#region Properties

    width = 0;
    height = 0;
    dpi = Math.max(1, devicePixelRatio);

    // Wave parameters
    turbulence = Math.PI * 6.0;
    pointSize = 1 * this.dpi;
    pointSizeCutoff = 5;
    speed = 10;
    waveHeight = 5;
    distance = 3;

    fov = (60 * Math.PI) / 180;
    aspectRatio = 1;
    cameraZ = 95;

    lodThreshold = this.cameraZ * 0.9;

    /**
     * Tangent of the field of view, i.e the angle between the horizon and the camera
     */
    f = Math.tan(Math.PI * 0.5 - 0.5 * this.fov);

    /**
     * Flat array storing particle data:
     * [baseX, baseZ, baseY, r, g, b, a, size, perspectiveSize, halfSize, perspectiveDepthAlpha]
     * @type {Float32Array}
     */
    #particleData = new Float32Array(0);
    #particleOffsetCount = this.#particleData.length / ParticleOffsets.PARTICLE_SIZE;

    // Performance optimizations
    /**
     * @type {ImageData}
     */
    // @ts-expect-error - Assigned in resize listener
    #buffer;

    /**
     * @type {Uint8ClampedArray}
     */
    // @ts-expect-error - Assigned in resize listener
    #sample;

    #gridWidth = 0;
    #gridDepth = 0;
    #fieldWidth = 0;
    #fieldHeight = 0;
    #fieldDepth = 0;

    #relativeWidth = 0;
    #relativeHeight = 0;

    // Frustum culling bounds
    #frustumLeft = 0;
    #frustumRight = 0;
    #frustumTop = 0;
    #frustumBottom = 0;
    #frustumNear = 0;
    #frustumFar = 0;

    /**
     * @type {HTMLCanvasElement}
     */
    #canvas;

    /**
     * @type {CanvasRenderingContext2D}
     */
    #ctx;

    /**
     * The method to use to draw the waves.
     * @type {(x: number, y: number, halfSize: number, r: number, g: number, b: number, a: number) => void}
     */
    #drawShape;

    //#endregion

    //#region Lifecycle

    /**
     * @param {string | HTMLCanvasElement} target
     * @param {"circle" | "triangle"} shape
     */
    constructor(target, shape = "circle") {
        const element = typeof target === "string" ? document.querySelector(target) : target;

        if (!(element instanceof HTMLCanvasElement)) {
            throw new TypeError("Invalid canvas element");
        }

        this.#canvas = element;

        const ctx = this.#canvas.getContext("2d", {
            alpha: false,
            desynchronized: true,
        });

        if (!ctx) {
            throw new TypeError("Failed to get 2D context");
        }

        this.#ctx = ctx;

        // We apply a background color to the canvas element itself for a slight performance boost.
        this.#canvas.style.background = getComputedStyle(document.body).backgroundColor;
        // All containment rules are applied to the element to further improve performance.
        this.#canvas.style.contain = "strict";
        // Applying a null transform on the canvas forces the browser to use the GPU for rendering.
        this.#canvas.style.willChange = "transform";
        this.#canvas.style.transform = "translate3d(0, 0, 0)";
        this.#canvas.style.pointerEvents = "none";

        this.#drawShape =
            shape === "circle" ? this.#drawCircleParticle : this.#drawTriangleParticle;

        window.addEventListener("resize", this.refresh);
        const colorSchemeChangeListener = window.matchMedia("(prefers-color-scheme: dark)");

        colorSchemeChangeListener.addEventListener("change", this.refresh);
    }

    refresh = () => {
        const container = this.#canvas.parentElement;

        if (!container) return;

        this.width = container.offsetWidth;
        this.height = container.offsetHeight;
        this.aspectRatio = this.width / this.height;

        this.#relativeWidth = this.width * this.dpi;
        this.#relativeHeight = this.height * this.dpi;

        this.#canvas.width = this.#relativeWidth;
        this.#canvas.height = this.#relativeHeight;

        this.#canvas.style.width = this.width + "px";
        this.#canvas.style.height = this.height + "px";

        this.#ctx.scale(this.dpi, this.dpi);

        this.#buffer = this.#ctx.createImageData(this.width * this.dpi, this.height * this.dpi);

        this.#gridWidth = 300 * this.aspectRatio;
        this.#gridDepth = 300;

        this.#fieldWidth = this.#gridWidth;
        this.#fieldHeight = this.waveHeight * this.aspectRatio;
        this.#fieldDepth = this.#gridDepth;

        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

        if (prefersReducedMotion.matches) {
            this.speed = 5;
        }

        this.#calculateFrustumBounds();
        this.#generateParticles();

        this.#ctx.fillStyle = getComputedStyle(document.body).backgroundColor;
        this.#ctx.fillRect(0, 0, this.#relativeWidth, this.#relativeHeight);

        // Grab a single pixel from the canvas and store it for later blending.
        this.#sample = this.#ctx.getImageData(0, 0, 1, 1).data;
    };

    //#endregion

    //#region Frustum Culling

    #calculateFrustumBounds() {
        const halfFov = this.fov / 2;
        const tanHalfFov = Math.tan(halfFov);

        this.#frustumNear = 1;
        this.#frustumFar = this.cameraZ + this.#gridDepth;

        const nearHeight = 2 * this.#frustumNear * tanHalfFov;
        const nearWidth = nearHeight * this.aspectRatio;

        this.#frustumLeft = -nearWidth / 2;
        this.#frustumRight = nearWidth / 2;
        this.#frustumTop = -1 * (this.aspectRatio / this.height);
        this.#frustumBottom = -1.25 * nearHeight;
    }

    /**
     * Test if a 3D point is within the view frustum
     * @param {number} x - World X coordinate
     * @param {number} y - World Y coordinate
     * @param {number} z - World Z coordinate
     * @returns {boolean}
     */
    #isInFrustum(x, y, z) {
        const projectedZ = z + this.cameraZ;

        // Behind camera or too far
        if (projectedZ <= this.#frustumNear || projectedZ > this.#frustumFar) {
            return false;
        }

        // Calculate frustum bounds at this depth
        const scale = projectedZ / this.#frustumNear;
        const left = this.#frustumLeft * scale;
        const right = this.#frustumRight * scale;
        const top = this.#frustumTop * scale;
        const bottom = this.#frustumBottom * scale;

        // Test if point is within frustum bounds
        return x >= left && x <= right && y >= bottom && y <= top;
    }

    //#endregion

    //#region Particle Generation

    #generateParticles() {
        const particleCount =
            Math.floor(this.#gridWidth / this.distance) *
            Math.floor(this.#gridDepth / this.distance);

        this.#particleData = new Float32Array(particleCount * ParticleOffsets.PARTICLE_SIZE);
        this.#particleOffsetCount = this.#particleData.length / ParticleOffsets.PARTICLE_SIZE;

        let particleIndex = 0;

        for (let x = 0; x < this.#gridWidth; x += this.distance) {
            const baseX = Math.round(-this.#gridWidth / 2 + x);

            for (let z = 0; z < this.#gridDepth; z += this.distance) {
                const baseZ = -this.#gridDepth / 2 + z;
                const depthFactor = (z / this.#gridDepth) * 0.9;
                const horizonFactor = (x / this.#gridWidth) * 1;

                // Pre-calculate perspective size based on fixed depth
                const projectedZ = baseZ + this.cameraZ;
                const baseSize = (this.height / 250) * this.pointSize * this.dpi;

                // More exaggerated scaling with logarithmic falloff for horizon effect
                const normalizedDepth = Math.max(0, (projectedZ - 50) / 200);
                // Log scale for dramatic falloff
                const logScale = Math.log(1 + normalizedDepth * 4) / Math.log(6);
                // Invert so closer = larger
                const distanceFactor = Math.max(0.05, 1 - logScale);
                const perspectiveSize = baseSize * distanceFactor * 3;

                const alpha = Math.max(Math.floor(z / this.#gridDepth), 0.85);
                const depthAlpha = Math.max(0.6, Math.pow(distanceFactor, 2));

                const offset = particleIndex * ParticleOffsets.PARTICLE_SIZE;

                // Store particle data in flat array
                this.#particleData[offset + ParticleOffsets.BASE_X] = baseX;
                this.#particleData[offset + ParticleOffsets.BASE_Z] = baseZ;
                this.#particleData[offset + ParticleOffsets.BASE_Y] = this.cameraZ * -0.4;
                this.#particleData[offset + ParticleOffsets.R] = Math.min(
                    Math.floor(253 / (depthFactor * horizonFactor)),
                    255,
                );
                this.#particleData[offset + ParticleOffsets.G] = Math.min(
                    Math.floor(75 / horizonFactor),
                    255,
                );
                this.#particleData[offset + ParticleOffsets.B] = Math.min(
                    Math.floor(45 / (depthFactor * horizonFactor * 2)),
                    255,
                );
                this.#particleData[offset + ParticleOffsets.A] = alpha;
                this.#particleData[offset + ParticleOffsets.SIZE] = baseSize;
                this.#particleData[offset + ParticleOffsets.PERSPECTIVE_SIZE] = perspectiveSize;
                this.#particleData[offset + ParticleOffsets.HALF_SIZE] = Math.max(
                    1,
                    Math.round(perspectiveSize / 1.5),
                );
                this.#particleData[offset + ParticleOffsets.PERSPECTIVE_DEPTH_ALPHA] =
                    depthAlpha ** 2;

                particleIndex++;
            }
        }
    }

    //#endregion

    //#region Projection

    /**
     * @param {number} x
     * @param {number} y
     * @param {number} z
     * @returns {{x: number, y: number, z: number} | null}
     */
    project3DTo2D(x, y, z) {
        const projectedX = (x * this.f) / this.aspectRatio;
        const projectedY = y * this.f;
        const projectedZ = z + this.cameraZ;

        if (projectedZ <= 0) return null;

        // Convert to screen coordinates
        // top of canvas is horizon (y=0), bottom is near

        const screenX = ((projectedX / projectedZ) * this.width) / 2 + this.width / 2;
        const screenY =
            this.height / 2 - ((projectedY / projectedZ) * this.height) / 2 - this.cameraZ * 2;

        return { x: screenX, y: screenY, z: projectedZ };
    }

    //#endregion

    //#region Rendering

    /**
     * @param {number} x
     * @param {number} z
     * @param {number} time
     * @returns {number}
     */
    calculateWaveY(x, z, time) {
        return (
            (Math.cos((x / this.#fieldWidth) * this.turbulence + time * this.speed) +
                Math.sin((z / this.#fieldDepth) * this.turbulence + time * this.speed)) *
            this.#fieldHeight
        );
    }

    /**
     * Draw a simple point particle (for distant objects)
     * @param {number} x
     * @param {number} y
     * @param {number} r
     * @param {number} g
     * @param {number} b
     * @param {number} a
     */
    // eslint-disable-next-line max-params
    #drawPointParticle(x, y, r, g, b, a) {
        const data = this.#buffer.data;
        const centerX = Math.round(x * this.dpi);
        const centerY = Math.round(y * this.dpi);
        const width = this.#relativeWidth;
        const height = this.#relativeHeight;

        if (centerX >= 0 && centerX < width && centerY >= 0 && centerY < height) {
            const index = (centerY * width + centerX) * 4;
            const alpha = Math.round(a * 255);
            const blendFactor = alpha * 1.25;

            data[index] = Math.min(255, data[index] + (r * blendFactor) / 255);
            data[index + 1] = Math.min(255, data[index + 1] + (g * blendFactor) / 255);
            data[index + 2] = Math.min(255, data[index + 2] + (b * blendFactor) / 255);
            data[index + 3] = 255;
        }
    }

    /**
     * Draw a hollow circle particle
     * @param {number} x
     * @param {number} y
     * @param {number} halfSize
     * @param {number} r
     * @param {number} g
     * @param {number} b
     * @param {number} a
     */
    // eslint-disable-next-line max-params
    #drawCircleParticle = (x, y, halfSize, r, g, b, a) => {
        const data = this.#buffer.data;
        const centerX = Math.round(x * this.dpi);
        const centerY = Math.round(y * this.dpi);

        const width = this.#relativeWidth;
        const height = this.#relativeHeight;

        const alpha = Math.round(a * 255);
        const radius = halfSize;

        // Draw hollow circle - just the outline
        for (let py = -radius; py <= radius; py++) {
            for (let px = -radius; px <= radius; px++) {
                const distance = Math.sqrt(px * px + py * py);

                // Only draw pixels that are on the circle edge (within 1 pixel of radius)
                if (distance >= radius - 1 && distance <= radius) {
                    const xPixel = centerX + px;
                    const yPixel = centerY + py;

                    if (xPixel >= 0 && xPixel < width && yPixel >= 0 && yPixel < height) {
                        const index = (yPixel * width + xPixel) * 4;
                        const blendFactor = alpha * 1.25;

                        // Additive blending for glow effect
                        data[index] = Math.min(255, data[index] + (r * blendFactor) / 255);
                        data[index + 1] = Math.min(255, data[index + 1] + (g * blendFactor) / 255);
                        data[index + 2] = Math.min(255, data[index + 2] + (b * blendFactor) / 255);
                        data[index + 3] = 255;
                    }
                }
            }
        }
    };

    /**
     * Draw an isosceles triangle particle
     * @param {number} x
     * @param {number} y
     * @param {number} halfSize
     * @param {number} r
     * @param {number} g
     * @param {number} b
     * @param {number} a
     */
    // eslint-disable-next-line max-params
    #drawTriangleParticle = (x, y, halfSize, r, g, b, a) => {
        const data = this.#buffer.data;
        const centerX = Math.round(x * this.dpi);
        const centerY = Math.round(y * this.dpi);

        const width = this.#relativeWidth;
        const height = this.#relativeHeight;

        const alpha = Math.round(a * 255);

        // Draw hollow isosceles triangle pointing up - just the outline
        for (let py = -halfSize; py <= halfSize; py++) {
            // Calculate max width at this height - steeper taper for more triangular shape
            // 0 at top, 1 at bottom
            const normalizedHeight = (py + halfSize) / (2 * halfSize);
            const triangleWidth = Math.round(halfSize * normalizedHeight);

            for (let px = -triangleWidth; px <= triangleWidth; px++) {
                // Only draw if on the edge (left edge, right edge, or bottom edge)
                const isLeftEdge = px === -triangleWidth;
                const isRightEdge = px === triangleWidth;
                const isBottomEdge = py === halfSize;

                if (isLeftEdge || isRightEdge || isBottomEdge) {
                    const xPixel = centerX + px;
                    const yPixel = centerY + py;

                    if (xPixel >= 0 && xPixel < width && yPixel >= 0 && yPixel < height) {
                        const index = (yPixel * width + xPixel) * 4;
                        const blendFactor = alpha * 1.25;

                        // Additive blending for glow effect
                        data[index] = Math.min(255, data[index] + (r * blendFactor) / 255);
                        data[index + 1] = Math.min(255, data[index + 1] + (g * blendFactor) / 255);
                        data[index + 2] = Math.min(255, data[index + 2] + (b * blendFactor) / 255);
                        data[index + 3] = 255;
                    }
                }
            }
        }
    };

    #render = (time = performance.now()) => {
        const timestamp = time / 6000;

        this.#buffer.data.fill(0);

        for (let i = 0; i < this.#particleOffsetCount; i++) {
            const offset = i * ParticleOffsets.PARTICLE_SIZE;

            const baseX = this.#particleData[offset + ParticleOffsets.BASE_X];
            const baseZ = this.#particleData[offset + ParticleOffsets.BASE_Z];
            const baseY = this.#particleData[offset + ParticleOffsets.BASE_Y];

            const waveY = this.calculateWaveY(baseX, baseZ, timestamp);
            const worldY = baseY + waveY;

            if (!this.#isInFrustum(baseX, worldY, baseZ)) {
                continue;
            }

            const projected = this.project3DTo2D(baseX, worldY, baseZ);

            if (
                !projected ||
                projected.x < -50 ||
                projected.x > this.width + 50 ||
                projected.y < 0 ||
                projected.y > this.height + 50
            ) {
                continue;
            }

            const distance = Math.abs(projected.z - this.cameraZ);
            const perspectiveSize = this.#particleData[offset + ParticleOffsets.PERSPECTIVE_SIZE];

            if (distance > this.lodThreshold || perspectiveSize < this.pointSizeCutoff) {
                this.#drawPointParticle(
                    projected.x,
                    projected.y,
                    this.#particleData[offset + ParticleOffsets.R],
                    this.#particleData[offset + ParticleOffsets.G],
                    this.#particleData[offset + ParticleOffsets.B],
                    this.#particleData[offset + ParticleOffsets.PERSPECTIVE_DEPTH_ALPHA],
                );
            } else {
                this.#drawShape(
                    projected.x,
                    projected.y,
                    this.#particleData[offset + ParticleOffsets.HALF_SIZE],
                    this.#particleData[offset + ParticleOffsets.R],
                    this.#particleData[offset + ParticleOffsets.G],
                    this.#particleData[offset + ParticleOffsets.B],
                    this.#particleData[offset + ParticleOffsets.PERSPECTIVE_DEPTH_ALPHA],
                );
            }
        }

        // Image data doesn't support blending, so we need to do it manually.

        for (let i = 0; i < this.#buffer.data.length; i += 4) {
            this.#buffer.data[i] ||= this.#sample[0];
            this.#buffer.data[i + 1] ||= this.#sample[1];
            this.#buffer.data[i + 2] ||= this.#sample[2];
            this.#buffer.data[i + 3] ||= this.#sample[3];
        }

        this.#ctx.putImageData(this.#buffer, 0, 0);

        this.#renderFrameID = requestAnimationFrame(this.#render);
    };

    //#endregion

    //#region Public Methods

    #renderFrameID = -1;

    play = () => {
        this.refresh();

        this.#render();
    };

    pause = () => {
        cancelAnimationFrame(this.#renderFrameID);
    };
}
