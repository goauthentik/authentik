import window from '../window';
import debounce from 'lodash/debounce';

var performance = window ? window.performance : null;

var pnow = performance && performance.now ? () => performance.now() : () => Date.now();

var raf = (function(){
  if( window ) {
    if( window.requestAnimationFrame ){
      return function( fn ){ window.requestAnimationFrame( fn ); };
    } else if( window.mozRequestAnimationFrame ){
      return function( fn ){ window.mozRequestAnimationFrame( fn ); };
    } else if( window.webkitRequestAnimationFrame ){
      return function( fn ){ window.webkitRequestAnimationFrame( fn ); };
    } else if( window.msRequestAnimationFrame ){
      return function( fn ){ window.msRequestAnimationFrame( fn ); };
    }
  }

  return function( fn ){
    if( fn ){
      setTimeout( function(){
        fn( pnow() );
      }, 1000 / 60 );
    }
  };
})();

export const requestAnimationFrame = fn => raf( fn );

export const performanceNow = pnow;

export const now = () => Date.now();

export { debounce };
