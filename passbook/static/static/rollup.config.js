import resolve from 'rollup-plugin-node-resolve';
import commonjs from 'rollup-plugin-commonjs';
import minifyHTML from 'rollup-plugin-minify-html-literals';
import { terser } from 'rollup-plugin-terser';
import sourcemaps from 'rollup-plugin-sourcemaps';
import typescript from '@rollup/plugin-typescript';

export default [{
  input: './src/main.ts',
  output: [
    {
      format: 'es',
      dir: 'passbook',
      sourcemap: true
    }
  ],
  plugins: [
    typescript(),
    resolve({browser: true}),
    commonjs(),
    sourcemaps(),
    minifyHTML(),
    terser(),
  ],
}];
