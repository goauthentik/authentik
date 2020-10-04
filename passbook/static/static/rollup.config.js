import resolve from 'rollup-plugin-node-resolve';
import commonjs from 'rollup-plugin-commonjs';
import minifyHTML from 'rollup-plugin-minify-html-literals';
import { terser } from 'rollup-plugin-terser';
import sourcemaps from 'rollup-plugin-sourcemaps';

export default [{
  input: './src/passbook.js',
  output: [
    {
      format: 'iife',
      dir: 'passbook',
      sourcemap: true,
    }
  ],

  plugins: [
    resolve({browser: true}),
    commonjs(),
    sourcemaps(),
    minifyHTML(),
    terser(),
  ],

  watch: {
    clearScreen: false,
  },
}];
