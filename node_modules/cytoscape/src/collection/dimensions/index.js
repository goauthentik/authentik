import * as util from '../../util';
import position from './position';
import bounds from './bounds';
import widthHeight from './width-height';
import edgePoints from './edge-points';

export default util.assign( {}, position, bounds, widthHeight, edgePoints );
