import breadthfirstLayout from './breadthfirst';
import circleLayout from './circle';
import concentricLayout from './concentric';
import coseLayout from './cose';
import gridLayout from './grid';
import nullLayout from './null';
import presetLayout from './preset';
import randomLayout from './random';

export default [
  { name: 'breadthfirst', impl: breadthfirstLayout },
  { name: 'circle', impl: circleLayout },
  { name: 'concentric',impl: concentricLayout },
  { name: 'cose', impl: coseLayout },
  { name: 'grid', impl: gridLayout },
  { name: 'null', impl: nullLayout },
  { name: 'preset', impl: presetLayout },
  { name: 'random', impl: randomLayout }
];
