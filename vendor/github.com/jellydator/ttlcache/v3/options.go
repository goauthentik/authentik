package ttlcache

import "time"

// Option sets a specific cache option.
type Option[K comparable, V any] interface {
	apply(opts *options[K, V])
}

// optionFunc wraps a function and implements the Option interface.
type optionFunc[K comparable, V any] func(*options[K, V])

// apply calls the wrapped function.
func (fn optionFunc[K, V]) apply(opts *options[K, V]) {
	fn(opts)
}

// options holds all available cache configuration options.
type options[K comparable, V any] struct {
	capacity          uint64
	ttl               time.Duration
	loader            Loader[K, V]
	disableTouchOnHit bool
}

// applyOptions applies the provided option values to the option struct.
func applyOptions[K comparable, V any](v *options[K, V], opts ...Option[K, V]) {
	for i := range opts {
		opts[i].apply(v)
	}
}

// WithCapacity sets the maximum capacity of the cache.
// It has no effect when passing into Get().
func WithCapacity[K comparable, V any](c uint64) Option[K, V] {
	return optionFunc[K, V](func(opts *options[K, V]) {
		opts.capacity = c
	})
}

// WithTTL sets the TTL of the cache.
// It has no effect when passing into Get().
func WithTTL[K comparable, V any](ttl time.Duration) Option[K, V] {
	return optionFunc[K, V](func(opts *options[K, V]) {
		opts.ttl = ttl
	})
}

// WithLoader sets the loader of the cache.
// When passing into Get(), it sets an epheral loader that
// is used instead of the cache's default one.
func WithLoader[K comparable, V any](l Loader[K, V]) Option[K, V] {
	return optionFunc[K, V](func(opts *options[K, V]) {
		opts.loader = l
	})
}

// WithDisableTouchOnHit prevents the cache instance from
// extending/touching an item's expiration timestamp when it is being
// retrieved.
// When passing into Get(), it overrides the default value of the
// cache.
func WithDisableTouchOnHit[K comparable, V any]() Option[K, V] {
	return optionFunc[K, V](func(opts *options[K, V]) {
		opts.disableTouchOnHit = true
	})
}
