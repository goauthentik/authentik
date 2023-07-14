# 2.11.0 (December 2021)

#64: @DoubeDi added a method `GetItems` to retrieve all items in the cache. This method also triggers all callbacks associated with a normal `Get`

## API changes:

// GetItems returns a copy of all items in the cache. Returns nil when the cache has been closed.
func (cache *Cache) GetItems() map[string]interface{} {

# 2.10.0 (December 2021)

#62 : @nikhilk1701 found a memory leak where removed items are not directly eligible for garbage collection. There are no API changes.

# 2.9.0 (October 2021)

#55,#56,#57 : @chenyahui was on fire and greatly improved the peformance of the library. He also got rid of the blocking call to expirationNotification, making the code run twice as fast in the benchmarks!

# 2.8.1 (September 2021)

#53 : Avoids recalculation of TTL value returned in API when TTL is extended. by @iczc

# 2.8.0 (August 2021)

#51 : The call GetWithTTL(key string) (interface{}, time.Duration, error) is added so that you can retrieve an item, and also know the remaining TTL. Thanks to @asgarciap for contributing.

# 2.7.0 (June 2021)

#46 : got panic

A panic occured in a line that checks the maximum amount of items in the cache. While not definite root cause has been found, there is indeed the possibility of crashing an empty cache if the cache limit is set to 'zero' which codes for infinite. This would lead to removal of the first item in the cache which would panic on an empty cache.

Fixed this by applying the global cache lock to all configuration options as well.

# 2.6.0 (May 2021)

#44 : There are no API changes, but a contribution was made to use https://pkg.go.dev/golang.org/x/sync/singleflight as a way to provide everybody waiting for a key with that key when it's fetched. 

This removes some complexity from the code and will make sure that all callers will get a return value even if there's high concurrency and low TTL (as proven by the test that was added).

# 2.5.0 (May 2021)

## API changes:

* #39 : Allow custom loader function for each key via `GetByLoader`

Introduce the `SimpleCache` interface for quick-start and basic usage.

# 2.4.0 (April 2021)

## API changes:

* #42 : Add option to get list of keys
* #40: Allow 'Touch' on items without other operation

// Touch resets the TTL of the key when it exists, returns ErrNotFound if the key is not present.
func (cache *Cache) Touch(key string) error 

// GetKeys returns all keys of items in the cache. Returns nil when the cache has been closed.
func (cache *Cache) GetKeys() []string 

# 2.3.0 (February 2021)

## API changes:

* #38: Added func (cache *Cache) SetExpirationReasonCallback(callback ExpireReasonCallback) This wil function will replace SetExpirationCallback(..) in the next major version.

# 2.2.0 (January 2021)

## API changes:

* #37 : a GetMetrics call is now available for some information on hits/misses etc.
*  #34 : Errors are now const

# 2.1.0 (October 2020)

## API changes

* `SetCacheSizeLimit(limit int)` a call  was contributed to set a cache limit. #35

# 2.0.0 (July 2020)

## Fixes #29, #30, #31

## Behavioural changes

* `Remove(key)` now also calls the expiration callback when it's set
* `Count()` returns zero when the cache is closed

## API changes

* `SetLoaderFunction` allows you to provide a function to retrieve data on missing cache keys.
* Operations that affect item behaviour such as `Close`, `Set`, `SetWithTTL`, `Get`, `Remove`, `Purge` now return an error with standard errors `ErrClosed` an `ErrNotFound` instead of a bool or nothing
* `SkipTTLExtensionOnHit` replaces `SkipTtlExtensionOnHit` to satisfy golint
* The callback types are now exported
