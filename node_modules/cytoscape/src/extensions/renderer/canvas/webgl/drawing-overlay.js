import { hashString } from '../../../../util/hash';


function fillStyle(color, opacity) {
  return `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${opacity})`;
}

export class OverlayUnderlayRenderer {

  constructor(r) {
    this.r = r;
  }

  getStyleKey(type, node) {
    const { shape, opacity, color } = this.getStyle(type, node);
    if(!shape)
      return null;
    const w = node.width();
    const h = node.height();
    const c = fillStyle(color, opacity);
    return hashString(`${shape}-${w}-${h}-${c}`); // TODO hack, not very efficient
  }

  isVisible(type, node) {
    const opacity = node.pstyle(`${type}-opacity`).value;
    return opacity > 0;
  }

  getStyle(type, node) {
    const opacity = node.pstyle(`${type}-opacity`).value;
    const color   = node.pstyle(`${type}-color`).value;
    const shape   = node.pstyle(`${type}-shape`).value;
    return { opacity, color, shape }; // TODO need to add radius at some point
  }

  getPadding(type, node) {
    return node.pstyle(`${type}-padding`).pfValue;
  }

  draw(type, context, node, bb) {
    if(!this.isVisible(type, node))
      return;

    const { r } = this;

    const w = bb.w;
    const h = bb.h;
    const x = w / 2;
    const y = h / 2;

    const { shape, color, opacity } = this.getStyle(type, node);

    context.save();
    context.fillStyle = fillStyle(color, opacity);
    if(shape === 'round-rectangle' || shape === 'roundrectangle') {
      r.drawRoundRectanglePath(context, x, y, w, h, 'auto');
    } else if(shape === 'ellipse') {
      r.drawEllipsePath(context, x, y, w, h);
    }
    context.fill();
    context.restore();
  }


}