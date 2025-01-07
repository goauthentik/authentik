import layout from './layout';
import renderer from './renderer';

export default [
  {
    type: 'layout',
    extensions: layout
  },

  {
    type: 'renderer',
    extensions: renderer
  }
];
