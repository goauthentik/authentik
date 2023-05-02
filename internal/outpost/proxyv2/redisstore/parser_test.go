// SPDX-FileCopyrightText: 2020 The Gitea Authors
// SPDX-License-Identifier: MIT

package redisstore

import (
	"net/url"
	"reflect"
	"testing"
	"time"

	"github.com/redis/go-redis/v9"
)

func uriMustGetRedisOptions(uri *url.URL) *redis.UniversalOptions {
	opts, err := getRedisOptions(uri)
	if err != nil {
		panic(err)
	}
	return opts
}

func TestRedisUsernameOpt(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/0")
	opts := uriMustGetRedisOptions(uri)

	if opts.Username != "redis" {
		t.Fail()
	}
}

func TestRedisUsernameArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/0?username=newredis")
	opts := uriMustGetRedisOptions(uri)

	if opts.Username != "newredis" {
		t.Fail()
	}
}

func TestRedisOnlyUsernameOpt(t *testing.T) {
	uri, _ := url.Parse("redis://redis:@myredis/0")
	opts := uriMustGetRedisOptions(uri)

	if opts.Username != "redis" {
		t.Fail()
	}
}


func TestRedisPasswordOpt(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/0")
	opts := uriMustGetRedisOptions(uri)

	if opts.Password != "password" {
		t.Fail()
	}
}

func TestRedisPasswordArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/0?password=newpassword")
	opts := uriMustGetRedisOptions(uri)

	if opts.Password != "newpassword" {
		t.Fail()
	}
}

func TestRedisOnlyPasswordOpt(t *testing.T) {
	uri, _ := url.Parse("redis://password@myredis/0")
	opts := uriMustGetRedisOptions(uri)

	if opts.Password != "password" {
		t.Fail()
	}
}

func TestRedisDatabaseArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://password@myredis?database=15")
	opts := uriMustGetRedisOptions(uri)

	if opts.DB != 15 {
		t.Fail()
	}
}

func TestRedisDBArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://password@myredis?db=10")
	opts := uriMustGetRedisOptions(uri)

	if opts.DB != 10 {
		t.Fail()
	}
}

func TestRedisAddrArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?addr=newmyredis")
	opts := uriMustGetRedisOptions(uri)

	if reflect.DeepEqual(opts.Addrs, []string{"newmyredis"}) {
		t.Fail()
	}
}

func TestRedisAddrsArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?addrs=newmyredis:1234,otherredis")
	opts := uriMustGetRedisOptions(uri)

	if reflect.DeepEqual(opts.Addrs, []string{"myredis", "newmyredis:1234", "otherredis"}) {
		t.Fail()
	}
}

func TestRedisMaxRetriesArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?maxretries=123")
	opts := uriMustGetRedisOptions(uri)

	if opts.MaxRetries != 123 {
		t.Fail()
	}
}

func TestRedisMinRetryBackoffArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?minretrybackoff=100s")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(100) * time.Second

	if opts.MinRetryBackoff != expectedValue {
		t.Fail()
	}
}

func TestRedisMaxRetryBackoffArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?maxretrybackoff=100s")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(100) * time.Second

	if opts.MaxRetryBackoff != expectedValue {
		t.Fail()
	}
}

func TestRedisDialTimeoutArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?dialtimeout=100s")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(100) * time.Second

	if opts.DialTimeout != expectedValue {
		t.Fail()
	}
}

func TestRedisReadTimeoutArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?readtimeout=100s")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(100) * time.Second

	if opts.ReadTimeout != expectedValue {
		t.Fail()
	}
}

func TestRedisWriteTimeoutArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?writetimeout=100s")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(100) * time.Second

	if opts.WriteTimeout != expectedValue {
		t.Fail()
	}
}

func TestRedisPoolTimeoutArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?pooltimeout=100s")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(100) * time.Second

	if opts.PoolTimeout != expectedValue {
		t.Fail()
	}
}

func TestRedisPoolFIFOArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?poolfifo=true")
	opts := uriMustGetRedisOptions(uri)

	if opts.PoolFIFO != true {
		t.Fail()
	}
}

func TestRedisPoolFIFOArgOptFallback(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?poolfifo=abc")
	opts := uriMustGetRedisOptions(uri)

	if opts.PoolFIFO != false {
		t.Fail()
	}
}

func TestRedisPoolSizeArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?poolsize=32")
	opts := uriMustGetRedisOptions(uri)

	if opts.PoolSize != 32 {
		t.Fail()
	}
}

func TestRedisReadOnlyArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?readonly=true")
	opts := uriMustGetRedisOptions(uri)

	if opts.ReadOnly != true {
		t.Fail()
	}
}

func TestRedisRouteByLatencyArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?routebylatency=true")
	opts := uriMustGetRedisOptions(uri)

	if opts.RouteByLatency != true {
		t.Fail()
	}
}

func TestRedisRouteRandomlyArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?routerandomly=true")
	opts := uriMustGetRedisOptions(uri)

	if opts.RouteRandomly != true {
		t.Fail()
	}
}

func TestRedisSentinelMasterIDArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?sentinelmasterid=themaster")
	opts := uriMustGetRedisOptions(uri)

	if opts.MasterName != "themaster" {
		t.Fail()
	}
}

func TestRedisMasternameArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?mastername=themaster")
	opts := uriMustGetRedisOptions(uri)

	if opts.MasterName != "themaster" {
		t.Fail()
	}
}

func TestRedisMinIdleConnsArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?minidleconns=123")
	opts := uriMustGetRedisOptions(uri)

	if opts.MinIdleConns != 123 {
		t.Fail()
	}
}

func TestRedisMaxIdleConnsArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?maxidleconns=52")
	opts := uriMustGetRedisOptions(uri)

	if opts.MaxIdleConns != 52 {
		t.Fail()
	}
}

func TestRedisMaxRedirectsArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?maxredirects=36")
	opts := uriMustGetRedisOptions(uri)

	if opts.MaxRedirects != 36 {
		t.Fail()
	}
}

func TestSkipVerifyArgOpt(t *testing.T) {
	uri, _ := url.Parse("rediss://myredis/0?skipverify=true")
	tlsConfig := getRedisTLSOptions(uri)

	if !tlsConfig.InsecureSkipVerify {
		t.Fail()
	}
}

func TestInsecureSkipVerifyArgOpt(t *testing.T) {
	uri, _ := url.Parse("rediss://myredis/0?insecureskipverify=true")
	tlsConfig := getRedisTLSOptions(uri)

	if !tlsConfig.InsecureSkipVerify {
		t.Fail()
	}
}

func TestTimeoutArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?timeout=100m")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(100) * time.Minute

	if opts.DialTimeout != expectedValue || opts.ReadTimeout != expectedValue {
		t.Fail()
	}
}

func TestTimeoutArgOptFallback(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?timeout=1y")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(0)

	if opts.DialTimeout != expectedValue || opts.ReadTimeout != expectedValue {
		t.Fail()
	}
}

func TestRedisSentinelUsernameArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis+sentinel://redis:password@myredis/0?sentinelusername=suser&sentinelpassword=spass")
	opts := uriMustGetRedisOptions(uri).Failover()

	if opts.SentinelUsername != "suser" {
		t.Fail()
	}
}

func TestRedisSentinelPasswordArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis+sentinel://redis:password@myredis/0?sentinelusername=suser&sentinelpassword=spass")
	opts := uriMustGetRedisOptions(uri).Failover()

	if opts.SentinelPassword != "spass" {
		t.Fail()
	}
}

func TestRedisDatabaseIndexTcp(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/12")
	opts := uriMustGetRedisOptions(uri)

	if opts.DB != 12 {
		t.Fail()
	}
}

func TestRedisDatabaseIndexUnix(t *testing.T) {
	uri, _ := url.Parse("redis+socket:///var/run/redis.sock?database=12")
	opts := uriMustGetRedisOptions(uri)

	if opts.DB != 12 {
		t.Fail()
	}
}
