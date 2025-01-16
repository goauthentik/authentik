import * as util from './webgl-util';
import * as cyutil from '../../../../util';
import { mat3 } from 'gl-matrix';

// A "texture atlas" is a big image/canvas, and sections of it are used as textures for nodes/labels.

/**
 * A single square texture atlas (also known as a "sprite sheet").
 */
export class Atlas {

  constructor(r, opts) {
    this.debugID = Math.floor(Math.random() * 10000);
    this.r = r;

    this.atlasSize = opts.webglTexSize;
    this.rows = opts.webglTexRows;
    this.enableWrapping = opts.enableWrapping;

    this.texHeight = Math.floor(this.atlasSize / this.rows);
    this.maxTexWidth = this.atlasSize;

    this.texture = null;
    this.canvas = null;
    this.needsBuffer = true;

    // a "location" is an object with a row and x fields
    this.freePointer = { x: 0, row: 0 };

    // map from the style key to the row/x where the texture starts
    // if the texture wraps then there's a second location
    this.keyToLocation = new Map(); // styleKey -> [ location, location ]

    this.canvas  = opts.createTextureCanvas(r, this.atlasSize, this.atlasSize);
    this.scratch = opts.createTextureCanvas(r, this.atlasSize, this.texHeight, 'scratch');
  }

  getKeys() {
    return new Set(this.keyToLocation.keys());
  }

  getScale({ w, h }) {
    const { texHeight, maxTexWidth } = this;
    // try to fit to the height of a row
    let scale = texHeight / h;  // TODO what about pixelRatio?
    let texW = w * scale;
    let texH = h * scale;
    // if the scaled width is too wide then scale to fit max width instead
    if(texW > maxTexWidth) {
      scale = maxTexWidth / w;
      texW = w * scale;
      texH = h * scale;
    }
    return { scale, texW, texH };
  }


  draw(key, bb, doDrawing) {
    const { atlasSize, rows, texHeight } = this;
    const { scale, texW, texH } = this.getScale(bb);
    
    const locations = [ null, null ];

    const drawAt = (location, canvas) => {
      if(doDrawing && canvas) {
        const { context } = canvas;
        const { x, row } = location;
        const xOffset = x;
        const yOffset = texHeight * row;

        context.save();
        context.translate(xOffset, yOffset);
        context.scale(scale, scale);
        doDrawing(context, bb);
        context.restore();
      }
    };

    const drawNormal = () => {
      // don't need to wrap, draw directly on the canvas
      drawAt(this.freePointer, this.canvas);
            
      locations[0] = {
        x: this.freePointer.x,
        y: this.freePointer.row * texHeight,
        w: texW,
        h: texH
      };
      locations[1] = {  // indlude a second location with a width of 0, for convenience
        x: this.freePointer.x + texW,
        y: this.freePointer.row * texHeight,
        w: 0,
        h: texH
      }; 

      // move the pointer to the end of the texture
      this.freePointer.x += texW;
      if(this.freePointer.x == atlasSize) {
        // move to the next row
        // TODO what if there is no next row???
        this.freePointer.x = 0;
        this.freePointer.row++;
      }
    };

    const drawWrapped = () => {
      const { scratch, canvas } = this;

      // Draw to the scratch canvas
      scratch.clear();
      drawAt({ x:0, row:0 }, scratch);

      const firstTexW = atlasSize - this.freePointer.x;
      const secondTexW = texW - firstTexW;
      const h = texHeight;

      { // copy first part of scratch to the first texture
        const dx = this.freePointer.x;
        const dy = this.freePointer.row * texHeight;
        const w = firstTexW;
        
        canvas.context.drawImage(scratch, 
          0,  0,  w, h, 
          dx, dy, w, h
        );
        
        locations[0] = { 
          x: dx, 
          y: dy, 
          w: w, 
          h: texH 
        };
      }
      { // copy second part of scratch to the second texture
        const sx = firstTexW;
        const dy = (this.freePointer.row + 1) * texHeight;
        const w = secondTexW;

        if(canvas) {
          canvas.context.drawImage(scratch, 
            sx, 0, w, h, 
            0, dy, w, h
          );
        }

        locations[1] = { 
          x: 0, 
          y: dy,
          w: w,  
          h: texH 
        };
      }

      this.freePointer.x = secondTexW;
      this.freePointer.row++;
    };

    const moveToStartOfNextRow = () => {
      this.freePointer.x = 0;
      this.freePointer.row++;
    };

    if(this.freePointer.x + texW <= atlasSize) { // There's enough space in the current row
      drawNormal();
    } else if(this.freePointer.row >= rows-1) { // Need to move to the next row, but there are no more rows, atlas is full.
      return false;
    } else if(this.freePointer.x === atlasSize) { // happen to be right at end of current row
      moveToStartOfNextRow();
      drawNormal();
    } else if(this.enableWrapping) { // draw part of the texture to the end of the curent row, then wrap to the next row
      drawWrapped();
    } else { // move to the start of the next row, then draw normally
      moveToStartOfNextRow();
      drawNormal();
    }

    this.keyToLocation.set(key, locations);
    this.needsBuffer = true;
    return locations;
  }

  getOffsets(key) {
    return this.keyToLocation.get(key);
  }

  isEmpty() {
    return this.freePointer.x === 0 && this.freePointer.row === 0;
  }

  canFit(bb) {
    const { atlasSize, rows } = this;
    const { texW } = this.getScale(bb);
    if(this.freePointer.x + texW > atlasSize) { // need to wrap
      return this.freePointer.row < rows - 1; // return true if there's a row to wrap to
    }
    return true;
  }

  bufferIfNeeded(gl) {
    if(!this.texture) {
      this.texture = util.createTexture(gl, this.debugID);
    }
    if(this.needsBuffer) {
      this.texture.buffer(this.canvas);
      this.needsBuffer = false;
    }
  }

  dispose() {
    if(this.texture) {
      this.texture.deleteTexture();
      this.texture = null;
      this.needsBuffer = true;
    }
  }

}

/**
 * A collection of texture atlases, all of the same "render type". 
 * (Node body is an example of a render type.)
 * An AtlasCollection can also be notified when a texture is no longer needed, 
 * and it can garbage collect the unused textures.
 */
export class AtlasCollection {

  constructor(r, opts) {
    this.r = r;
    this.opts = opts;

    this.keyToIds = new Map();
    this.idToKey  = new Map();

    this.atlases = [];
    this.styleKeyToAtlas = new Map();
    this.styleKeyNeedsRedraw = new Set();

    this.forceGC = false;
  }

  getKeys() {
    return new Set(this.styleKeyToAtlas.keys());
  }

  getIdsFor(key) {
    let ids = this.keyToIds.get(key);
    if(!ids) {
      ids = new Set();
      this.keyToIds.set(key, ids);
    }
    return ids;
  }

  _createAtlas() {
    const { r, opts } = this;
    return new Atlas(r, opts);
  }

  _getScratchCanvas() {
    if(!this.scratch) {
      const { r, opts } = this;
      const atlasSize = opts.webglTexSize;
      const texHeight = Math.floor(atlasSize / opts.webglTexRows);
      this.scratch = opts.createTextureCanvas(r, atlasSize, texHeight, 'scratch');
    }
    return this.scratch;
  }

  draw(id, key, bb, doDrawing) {
    if(this.styleKeyNeedsRedraw.has(key)) {
      this.styleKeyNeedsRedraw.delete(key);
      this.deleteKey(id, key);
      // We need to mark the atlas as needing GC because the key will be mapped to
      // this atlas or a new atlas, so the key itself won't be marked for GC.
      const atlas = this.styleKeyToAtlas.get(key);
      if(atlas) {
        atlas.forceGC = true;
      }
      this.styleKeyToAtlas.delete(key);
    }

    let atlas = this.styleKeyToAtlas.get(key);
    if(!atlas) {
      // This is a simplistic way of finding an atlas. 
      // May waste space at the end of the atalas if the element doesn't fit.
      atlas = this.atlases[this.atlases.length - 1];
      if(!atlas || !atlas.canFit(bb)) {
        atlas = this._createAtlas();
        this.atlases.push(atlas);
      }

      atlas.draw(key, bb, doDrawing);

      this.styleKeyToAtlas.set(key, atlas);
      this.getIdsFor(key).add(id);
      this.idToKey.set(id, key);
    }
    return atlas;
  }

  getAtlas(key) {
    return this.styleKeyToAtlas.get(key);
  }

  hasAtlas(key) {
    return this.styleKeyToAtlas.has(key);
  }

  deleteKey(id, key) {
    this.idToKey.delete(id);
    this.getIdsFor(key).delete(id);
  }

  checkKeyIsInvalid(id, newKey) {
    if(!this.idToKey.has(id))
      return false;
    const oldKey = this.idToKey.get(id);
    if(oldKey != newKey) {
      this.deleteKey(id, oldKey);
      return true;
    }
    return false;
  }

  _getKeysToCollect() {
    const markedKeys = new Set();
    for(const key of this.styleKeyToAtlas.keys()) {
      if(this.getIdsFor(key).size == 0) {
        markedKeys.add(key);
      }
    }
    return markedKeys;
  }

  /**
   * TODO dispose of the old atlas and texture
   */
  gc() {
    const forceGC = this.atlases.some(atlas => atlas.forceGC);
    const markedKeys = this._getKeysToCollect();

    if(markedKeys.size === 0 && !forceGC) {
      console.log("nothing to garbage collect");
      return;
    }

    const newAtlases = [];
    const newStyleKeyToAtlas = new Map();

    let newAtlas = null;

    for(const atlas of this.atlases) {
      const keys = atlas.getKeys();
      
      const keysToCollect = intersection(markedKeys, keys);

      if(keysToCollect.size === 0 && !atlas.forceGC) {
        newAtlases.push(atlas);
        keys.forEach(k => newStyleKeyToAtlas.set(k, atlas));
        continue;
      } 

      if(!newAtlas) {
        newAtlas = this._createAtlas();
        newAtlases.push(newAtlas);
      }

      for(const key of keys) {
        if(!keysToCollect.has(key)) {
          const [ s1, s2 ] = atlas.getOffsets(key);
          if(!newAtlas.canFit({ w: s1.w + s2.w, h: s1.h })) {
            newAtlas = this._createAtlas();
            newAtlases.push(newAtlas);
          }
          this._copyTextureToNewAtlas(key, atlas, newAtlas);
          newStyleKeyToAtlas.set(key, newAtlas);
        }
      }
    }

    this.atlases = newAtlases;
    this.styleKeyToAtlas = newStyleKeyToAtlas;
  }


  _copyTextureToNewAtlas(key, oldAtlas, newAtlas) {
    const [ s1, s2 ] = oldAtlas.getOffsets(key);

    if(s2.w === 0) { // the texture does not wrap, draw directly to new atlas
      newAtlas.draw(key, s1, context => {
        context.drawImage(oldAtlas.canvas, 
          s1.x, s1.y, s1.w, s1.h, 
          0,    0,    s1.w, s1.h
        );
      });
    } else {
      // the texture wraps, first draw both parts to a scratch canvas
      const scratch = this._getScratchCanvas();
      scratch.clear();
      scratch.context.drawImage(oldAtlas.canvas, 
        s1.x, s1.y, s1.w, s1.h,
        0,    0,    s1.w, s1.h
      );
      scratch.context.drawImage(oldAtlas.canvas, 
        s2.x, s2.y, s2.w, s2.h,
        s1.w, 0,    s2.w, s2.h
      );

      // now draw the scratch to the new atlas
      const w = s1.w + s2.w;
      const h = s1.h;
      newAtlas.draw(key, { w, h }, context => {
        context.drawImage(scratch, 
          0, 0, w, h,
          0, 0, w, h   // the destination context has already been translated to the correct position
        );
      });
    }
  }


  getCounts() {
    return { 
      keyCount: this.styleKeyToAtlas.size,
      atlasCount: new Set(this.styleKeyToAtlas.values()).size
    };
  }

}


function intersection(set1, set2) {
  // TODO why no Set.intersection in node 16???
  if(set1.intersection)
    return set1.intersection(set2);
  else
    return new Set([...set1].filter(x => set2.has(x)));
}


/**
 * Used to manage batches of Atlases for drawing nodes and labels.
 * Supports different types of AtlasCollections for different render types,
 * for example 'node body' and 'node label' would be different render types.
 * Render types are kept separate because they will likely need to be garbage collected
 * separately and its not entierly guaranteed that their style keys won't collide.
 */
export class AtlasManager {

  constructor(r, globalOptions) {
    this.r = r;

    const opts = globalOptions;
    this.globalOptions = opts;
    this.maxAtlases = opts.webglTexPerBatch;
    this.atlasSize = opts.webglTexSize;
    
    this.renderTypes = new Map(); // string -> object
    this.maxAtlasesPerBatch = globalOptions.webglTexPerBatch;
    this.batchAtlases = [];

    this._cacheScratchCanvas(opts);
  }

  _cacheScratchCanvas(opts) {
    let prevW = -1;
    let prevH = -1;
    let scratchCanvas = null;

    const baseCreateTextureCanvas = opts.createTextureCanvas;

    opts.createTextureCanvas = (r, w, h, scratch) => {
      if(scratch) {
        if(!scratchCanvas || w != prevW || h != prevH) {
          prevW = w;
          prevH = h;
          scratchCanvas = baseCreateTextureCanvas(r, w, h);
        }
        return scratchCanvas;
      } else {
        return baseCreateTextureCanvas(r, w, h);
      }
    };
  }

  addRenderType(type, renderTypeOptions) {
    const atlasCollection = new AtlasCollection(this.r, this.globalOptions);
    const typeOpts = renderTypeOptions;
    this.renderTypes.set(type, cyutil.extend( { type, atlasCollection}, typeOpts ) );
  }

  getRenderTypes() {
    return [ ...this.renderTypes.values() ];
  }

  getRenderTypeOpts(type) {
    return this.renderTypes.get(type);
  }

  /** Marks textues associated with the element for garbage collection. */
  invalidate(eles, { forceRedraw=false, filterEle=()=>true, filterType=()=>true } = {}) {
    let gcNeeded = false;
    for(const ele of eles) {
      if(filterEle(ele)) {
        const id = ele.id();
        for(const opts of this.getRenderTypes()) {
          if(filterType(opts.type)) {
            const styleKey = opts.getKey(ele);
            if(forceRedraw) { 
              // when a node's background image finishes loading, the style key doesn't change but still needs to be redrawn
              opts.atlasCollection.deleteKey(id, styleKey);
              opts.atlasCollection.styleKeyNeedsRedraw.add(styleKey);
              gcNeeded = true; // TODO is this too conservative?
            } else {
              gcNeeded |= opts.atlasCollection.checkKeyIsInvalid(id, styleKey);
            }
          }
        }
      }
    }
    return gcNeeded;
  }

  /** Garbage collect */
  gc() {
    for(const opts of this.getRenderTypes()) {
      opts.atlasCollection.gc();
    }
  }

  isRenderable(ele, type) {
    const opts = this.getRenderTypeOpts(type);
    return opts && opts.isVisible(ele);
  }

  startBatch() {
    this.batchAtlases = [];
  }

  getAtlasCount() {
    return this.batchAtlases.length;
  }

  getAtlases() {
    return this.batchAtlases;
  }

  getOrCreateAtlas(ele, bb, type) {
    const opts = this.renderTypes.get(type);
    const styleKey = opts.getKey(ele);
    const id = ele.id();

    // Draws the texture if needed.
    return opts.atlasCollection.draw(id, styleKey, bb, context => {
      opts.drawElement(context, ele, bb, true, true);
    });
  }

  getAtlasIndexForBatch(atlas) {
    let atlasID = this.batchAtlases.indexOf(atlas);
    if(atlasID < 0) {
      if(this.batchAtlases.length === this.maxAtlasesPerBatch) {
        return;
      }
      this.batchAtlases.push(atlas);
      atlasID = this.batchAtlases.length - 1;
    }
    return atlasID;
  }

  getIndexArray() {
    return Array.from({ length: this.maxAtlases }, (v,i) => i);
  }

  getAtlasInfo(ele, type) {
    const opts = this.renderTypes.get(type);
    const bb = opts.getBoundingBox(ele);
    const atlas = this.getOrCreateAtlas(ele, bb, type);
    const atlasID = this.getAtlasIndexForBatch(atlas);
    if(atlasID === undefined) {
      return undefined; // batch is full
    }
    const styleKey = opts.getKey(ele);
    const [ tex1, tex2 ] = atlas.getOffsets(styleKey);
    // This object may be passed back to setTransformMatrix()
    return { atlasID, tex:tex1, tex1, tex2, bb, type, styleKey };
  }

  canAddToCurrentBatch(ele, type) {
    if(this.batchAtlases.length === this.maxAtlasesPerBatch) { 
      // batch is full, is the atlas already part of this batch?
      const opts = this.renderTypes.get(type);
      const styleKey = opts.getKey(ele);
      const atlas = opts.atlasCollection.getAtlas(styleKey);
      // return true if there is an atlas and it is part of this batch already
      return atlas && this.batchAtlases.includes(atlas);
    }
    return true; // not full
  }

  /**
   * matrix is expected to be a 9 element array
   * this function follows same pattern as CRp.drawCachedElementPortion(...)
   */
  setTransformMatrix(matrix, atlasInfo, ele, first=true) {
    const { bb, type, tex1, tex2 } = atlasInfo;
    const opts = this.getRenderTypeOpts(type);

    const padding = opts.getPadding ? opts.getPadding(ele) : 0;

    let ratio = tex1.w / (tex1.w + tex2.w);
    if(!first) {
      ratio = 1 - ratio;
    }

    const adjBB = this.getAdjustedBB(bb, padding, first, ratio);

    let x, y;
    mat3.identity(matrix);

    const theta = opts.getRotation ? opts.getRotation(ele) : 0;
    if(theta !== 0) {
      const { x:sx, y:sy } = opts.getRotationPoint(ele);
      mat3.translate(matrix, matrix, [sx, sy]);
      mat3.rotate(matrix, matrix, theta);

      const offset = opts.getRotationOffset(ele);

      x = offset.x + adjBB.xOffset;
      y = offset.y;
    } else {
      x = adjBB.x1;
      y = adjBB.y1;
    }

    mat3.translate(matrix, matrix, [x, y]);
    mat3.scale(matrix, matrix, [adjBB.w, adjBB.h]);
  }

  getTransformMatrix(atlasInfo, ele, first=true) {
    const matrix = mat3.create();
    this.setTransformMatrix(matrix, atlasInfo, ele, first);
    return matrix;
  }

  /**
   * Adjusts a node or label BB to accomodate padding and split for wrapped textures.
   * @param bb - the original bounding box
   * @param padding - the padding to add to the bounding box
   * @param first - whether this is the first part of a wrapped texture
   * @param ratio - the ratio of the texture width of part of the text to the entire texture
   */
  getAdjustedBB(bb, padding, first, ratio) {
    let { x1, y1, w, h } = bb;

    if(padding) {
      x1 -= padding;
      y1 -= padding;
      w += 2 * padding;
      h += 2 * padding;
    }

    let xOffset = 0;
    const adjW = w * ratio;

    if(first && ratio < 1) {
      w = adjW;
    } else if(!first && ratio < 1) {
      xOffset = w - adjW;
      x1 += xOffset;
      w = adjW;
    }

    return { x1, y1, w, h, xOffset };
  }

  getDebugInfo() {
    const debugInfo = [];
    for(let [ type, opts ] of this.renderTypes) {
      const { keyCount, atlasCount } = opts.atlasCollection.getCounts();
      debugInfo.push({ type, keyCount, atlasCount });
    }
    return debugInfo;
  }

}
