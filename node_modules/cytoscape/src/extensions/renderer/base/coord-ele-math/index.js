import * as util from '../../../../util';

import coords from './coords';
import edgeArrows from './edge-arrows';
import edgeControlPoints from './edge-control-points';
import edgeEndpoints from './edge-endpoints';
import edgeProjection from './edge-projection';
import labels from './labels';
import nodes from './nodes';
import renderedStyle from './rendered-style';
import zOrdering from './z-ordering';

var BRp = {};

[
  coords,
  edgeArrows,
  edgeControlPoints,
  edgeEndpoints,
  edgeProjection,
  labels,
  nodes,
  renderedStyle,
  zOrdering
].forEach(function( props ){
  util.extend( BRp, props );
});

export default BRp;
