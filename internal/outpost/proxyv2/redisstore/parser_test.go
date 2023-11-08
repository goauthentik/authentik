// SPDX-FileCopyrightText: 2020 The Gitea Authors
// SPDX-License-Identifier: MIT

package redisstore

import (
	"net/url"
	"reflect"
	"strings"
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

func TestRedisCredentialsOpt(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/0")
	opts := uriMustGetRedisOptions(uri)

	if opts.Username != "redis" {
		t.Fail()
	}
	if opts.Password != "password" {
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

func TestOnlyRedisUsernameOpt(t *testing.T) {
	uri, _ := url.Parse("redis://redis:@myredis/0")
	opts := uriMustGetRedisOptions(uri)

	if opts.Username != "redis" {
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

func TestOnlyRedisPasswordOpt(t *testing.T) {
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

	if !reflect.DeepEqual(opts.Addrs, []string{"newmyredis", "myredis"}) {
		t.Fail()
	}
}

func TestRedisAddrArgNoHostOpt(t *testing.T) {
	uri, _ := url.Parse("redis:///0?addr=newmyredis")
	opts := uriMustGetRedisOptions(uri)

	if !reflect.DeepEqual(opts.Addrs, []string{"newmyredis"}) {
		t.Fail()
	}
}

func TestRedisAddrNoArgNoHostOpt(t *testing.T) {
	uri, _ := url.Parse("redis:///0")
	universalClient, err := GetRedisClient(uri)
	client, ok := universalClient.(*redis.Client)

	if err != nil || !ok || !reflect.DeepEqual(client.Options().Addr, "127.0.0.1:6379") {
		t.Fail()
	}
}

func TestRedisAddrNoArgNoHostFailoverOpt(t *testing.T) {
	uri, _ := url.Parse("redis+sentinel:///0?mastername=mymaster")
	opts := uriMustGetRedisOptions(uri).Failover()

	if !reflect.DeepEqual(opts.SentinelAddrs, []string{"127.0.0.1:26379"}) {
		t.Fail()
	}
}

func TestRedisAddrNoArgNoHostClusterOpt(t *testing.T) {
	uri, _ := url.Parse("redis+cluster:///0")
	opts := uriMustGetRedisOptions(uri).Cluster()

	if !reflect.DeepEqual(opts.Addrs, []string{"127.0.0.1:6379"}) {
		t.Fail()
	}
}

func TestRedisAddrsArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?addrs=newmyredis:1234,otherredis")
	opts := uriMustGetRedisOptions(uri)

	if !reflect.DeepEqual(opts.Addrs, []string{"newmyredis:1234", "otherredis", "myredis"}) {
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

func TestRedisMaxRetriesNegativeArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?maxretries=-432")
	universalClient, err := GetRedisClient(uri)
	client, ok := universalClient.(*redis.Client)

	if err != nil || !ok || !reflect.DeepEqual(client.Options().MaxRetries, 0) {
		t.Fail()
	}
}

func TestRedisMaxRetriesDefaultArgOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0")
	universalClient, err := GetRedisClient(uri)
	client, ok := universalClient.(*redis.Client)

	if err != nil || !ok || !reflect.DeepEqual(client.Options().MaxRetries, 3) {
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
	// Setting to zero will force the default value to be used (go-redis)
	uri, _ := url.Parse("redis://myredis/0?timeout=1y")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(0)

	if opts.DialTimeout != expectedValue || opts.ReadTimeout != expectedValue {
		t.Fail()
	}
}

func TestRedisSentinelCredentialsOpt(t *testing.T) {
	uri, _ := url.Parse("redis+sentinel://redis:password@myredis/0?mastername=mymaster&sentinelusername=suser&sentinelpassword=spass")
	opts := uriMustGetRedisOptions(uri).Failover()

	if opts.SentinelUsername != "suser" {
		t.Fail()
	}
	if opts.SentinelPassword != "spass" {
		t.Fail()
	}
}

func TestRedisSentinelNoMasternameOpt(t *testing.T) {
	uri, _ := url.Parse("redis+sentinel://myredis/0")
	_, err := getRedisOptions(uri)

	if err == nil || err.Error() != "no mastername provided for sentinel configuration" {
		t.Fail()
	}
}

func TestRedisUnknownOpt(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?notanarg=4")
	_, err := getRedisOptions(uri)

	if err == nil || err.Error() != "detected unknown configuration option 'notanarg'" {
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

func TestRedisDatabaseIndexInvalid(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/invalid")
	_, err := getRedisOptions(uri)

	if err == nil || err.Error() != "provided database identifier 'invalid' is not a valid integer" {
		t.Fail()
	}
}

func TestRedisDatabaseIndexSocket(t *testing.T) {
	uri, _ := url.Parse("redis+socket:///var/run/redis.sock?database=12")
	opts := uriMustGetRedisOptions(uri)

	if opts.DB != 12 {
		t.Fail()
	}
}

func TestGetRedisClientErrorPassthrough(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/invalid")
	_, err := GetRedisClient(uri)

	if err == nil || !strings.HasPrefix(err.Error(), "unable to read configuration from redis connection URL") {
		t.Fail()
	}
}

func TestIPv6HostAddress(t *testing.T) {
	uri, _ := url.Parse("redis://[2001:1:2:3:4::5]:6379/0")
	opts := uriMustGetRedisOptions(uri)

	if len(opts.Addrs) != 1 || opts.Addrs[0] != "[2001:1:2:3:4::5]:6379" {
		t.Fail()
	}
}

func TestConvertStringToDurationNoUnit(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?timeout=200")
	opts := uriMustGetRedisOptions(uri)
	expectedValue := time.Duration(200) * time.Second

	if opts.ReadTimeout != expectedValue {
		t.Fail()
	}
}

func TestConvertStringToDurationNegative(t *testing.T) {
	// Setting to -1 will disable any timeout (go-redis)
	uri, _ := url.Parse("redis://myredis/0?timeout=-210s")
	opts := uriMustGetRedisOptions(uri)

	if opts.ReadTimeout != -1 {
		t.Fail()
	}
}

func TestConvertStringToDurationNoValue(t *testing.T) {
	// Setting to zero will force the default value to be used (go-redis)
	uri, _ := url.Parse("redis://myredis/0?timeout=")
	opts := uriMustGetRedisOptions(uri)

	if opts.ReadTimeout != 0 {
		t.Fail()
	}
}

func TestConvertStringToBoolValid(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?readonly=False")
	opts := uriMustGetRedisOptions(uri)

	if opts.ReadOnly {
		t.Fail()
	}
}

func TestConvertStringToBoolInvalid(t *testing.T) {
	uri, _ := url.Parse("redis://myredis/0?readonly=TrUe")
	opts := uriMustGetRedisOptions(uri)

	if opts.ReadOnly {
		t.Fail()
	}
}

func TestRedisUnsupportedScheme(t *testing.T) {
	uri, _ := url.Parse("rediss+socket://test.sock")
	_, err := GetRedisClient(uri)

	if err == nil || err.Error() != "unknown scheme found in redis connection URL: rediss+socket" {
		t.Fail()
	}
}
