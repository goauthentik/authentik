import nullRenderer from './null';
import baseRenderer from './base';
import canvasRenderer from './canvas';

export default [
  { name: 'null', impl: nullRenderer },
  { name: 'base', impl: baseRenderer },
  { name: 'canvas', impl: canvasRenderer }
];
