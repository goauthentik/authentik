// Copyright 2020 The Gitea Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found at https://github.com/go-gitea/gitea/blob/main/LICENSE

package redisstore

import (
	"crypto/tls"
	"fmt"
	"net/url"
	"path"
	"strconv"
	"strings"
	"time"

	"github.com/go-redis/redis/v9"
)

var replacer = strings.NewReplacer("_", "", "-", "")

func GetRedisClient(url *url.URL) (redis.UniversalClient, error) {
	var client redis.UniversalClient

	opts, err := getRedisOptions(url)
	if err != nil {
		return nil, fmt.Errorf("unable to read configuration from redis connection URL: %w", err)
	}

	tlsConfig := getRedisTLSOptions(url)

	switch url.Scheme {
	case "redis+sentinels":
		fallthrough
	case "rediss+sentinel":
		opts.TLSConfig = tlsConfig
		fallthrough
	case "redis+sentinel":
		client = redis.NewFailoverClient(opts.Failover())
	case "redis+clusters":
		fallthrough
	case "rediss+cluster":
		opts.TLSConfig = tlsConfig
		fallthrough
	case "redis+cluster":
		client = redis.NewClusterClient(opts.Cluster())
	case "redis+socket":
		simpleOpts := opts.Simple()
		simpleOpts.Network = "unix"
		simpleOpts.Addr = path.Join(url.Host, url.Path)
		client = redis.NewClient(simpleOpts)
	case "rediss":
		opts.TLSConfig = tlsConfig
		fallthrough
	case "redis":
		client = redis.NewClient(opts.Simple())
	default:
		return nil, fmt.Errorf("unknown scheme found in redis connection URL: %s", url.Scheme)
	}

	return client, nil
}

// getRedisOptions pulls various configuration options based on the RedisUri format and converts them to go-redis's
// UniversalOptions fields. This function explicitly excludes fields related to TLS configuration, which is
// conditionally attached to this options struct before being converted to the specific type for the redis scheme being
// used, and only in scenarios where TLS is applicable (e.g. rediss://, redis+clusters://).
func getRedisOptions(uri *url.URL) (*redis.UniversalOptions, error) {
	opts := &redis.UniversalOptions{}

	// Handle username/password
	if password, ok := uri.User.Password(); ok {
		opts.Password = password
		// Username does not appear to be handled by redis.Options
		opts.Username = uri.User.Username()
	} else if uri.User.Username() != "" {
		// assume this is the password
		opts.Password = uri.User.Username()
	}

	// Now handle the uri query sets
	for k, v := range uri.Query() {
		switch replacer.Replace(strings.ToLower(k)) {
		case "addr":
			opts.Addrs = append(opts.Addrs, v...)
		case "addrs":
			opts.Addrs = append(opts.Addrs, strings.Split(v[0], ",")...)
		case "username":
			opts.Username = v[0]
		case "password":
			opts.Password = v[0]
		case "database":
			fallthrough
		case "db":
			opts.DB, _ = strconv.Atoi(v[0])
		case "maxretries":
			opts.MaxRetries, _ = strconv.Atoi(v[0])
		case "minretrybackoff":
			opts.MinRetryBackoff = valToTimeDuration(v)
		case "maxretrybackoff":
			opts.MaxRetryBackoff = valToTimeDuration(v)
		case "timeout":
			timeout := valToTimeDuration(v)
			if timeout != 0 {
				if opts.DialTimeout == 0 {
					opts.DialTimeout = timeout
				}
				if opts.ReadTimeout == 0 {
					opts.ReadTimeout = timeout
				}
			}
		case "dialtimeout":
			opts.DialTimeout = valToTimeDuration(v)
		case "readtimeout":
			opts.ReadTimeout = valToTimeDuration(v)
		case "writetimeout":
			opts.WriteTimeout = valToTimeDuration(v)
		case "poolfifo":
			opts.PoolFIFO, _ = strconv.ParseBool(v[0])
		case "poolsize":
			opts.PoolSize, _ = strconv.Atoi(v[0])
		case "pooltimeout":
			opts.PoolTimeout = valToTimeDuration(v)
		case "minidleconns":
			opts.MinIdleConns, _ = strconv.Atoi(v[0])
		case "maxidleconns":
			opts.MaxIdleConns, _ = strconv.Atoi(v[0])
		case "maxredirects":
			opts.MaxRedirects, _ = strconv.Atoi(v[0])
		case "readonly":
			opts.ReadOnly, _ = strconv.ParseBool(v[0])
		case "routebylatency":
			opts.RouteByLatency, _ = strconv.ParseBool(v[0])
		case "routerandomly":
			opts.RouteRandomly, _ = strconv.ParseBool(v[0])
		case "sentinelmasterid":
			fallthrough
		case "mastername":
			opts.MasterName = v[0]
		case "sentinelusername":
			opts.SentinelUsername = v[0]
		case "sentinelpassword":
			opts.SentinelPassword = v[0]
		}
	}

	if uri.Host != "" {
		opts.Addrs = append(opts.Addrs, strings.Split(uri.Host, ",")...)
	}

	// A redis connection string uses the path section of the URI in two different ways. In a TCP-based connection, the
	// path will be a database index to automatically have the client SELECT. In a Unix socket connection, it will be the
	// file path. We only want to try to coerce this to the database index when we're not expecting a file path so that
	// the error log stays clean.
	if uri.Path != "" && uri.Scheme != "redis+socket" {
		if db, err := strconv.Atoi(uri.Path[1:]); err == nil {
			opts.DB = db
		} else {
			return nil, fmt.Errorf("provided database identifier '%s' is not a valid integer", uri.Path)
		}
	}

	return opts, nil
}

// getRedisTlsOptions parses RedisUri TLS configuration parameters and converts them to the go TLS configuration
// equivalent fields.
func getRedisTLSOptions(uri *url.URL) *tls.Config {
	tlsConfig := &tls.Config{}

	skipverify := uri.Query().Get("skipverify")

	if len(skipverify) > 0 {
		skipverify, err := strconv.ParseBool(skipverify)
		if err == nil {
			tlsConfig.InsecureSkipVerify = skipverify
		}
	}

	insecureskipverify := uri.Query().Get("insecureskipverify")

	if len(insecureskipverify) > 0 {
		insecureskipverify, err := strconv.ParseBool(insecureskipverify)
		if err == nil {
			tlsConfig.InsecureSkipVerify = insecureskipverify
		}
	}

	return tlsConfig
}

func valToTimeDuration(vs []string) (result time.Duration) {
	var err error
	for _, v := range vs {
		result, err = time.ParseDuration(v)
		if err != nil {
			var val int
			val, err = strconv.Atoi(v)
			result = time.Duration(val)
		}
		if err == nil {
			return
		}
	}
	return result
}