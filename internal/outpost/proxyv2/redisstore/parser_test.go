// SPDX-FileCopyrightText: 2020 The Gitea Authors
// SPDX-License-Identifier: MIT

package redisstore

import (
	"net/url"
	"testing"

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

func TestRedisPasswordOpt(t *testing.T) {
	uri, _ := url.Parse("redis://redis:password@myredis/0")
	opts := uriMustGetRedisOptions(uri)

	if opts.Password != "password" {
		t.Fail()
	}
}

func TestSkipVerifyOpt(t *testing.T) {
	uri, _ := url.Parse("rediss://myredis/0?skipverify=true")
	tlsConfig := getRedisTLSOptions(uri)

	if !tlsConfig.InsecureSkipVerify {
		t.Fail()
	}
}

func TestInsecureSkipVerifyOpt(t *testing.T) {
	uri, _ := url.Parse("rediss://myredis/0?insecureskipverify=true")
	tlsConfig := getRedisTLSOptions(uri)

	if !tlsConfig.InsecureSkipVerify {
		t.Fail()
	}
}

func TestRedisSentinelUsernameOpt(t *testing.T) {
	uri, _ := url.Parse("redis+sentinel://redis:password@myredis/0?sentinelusername=suser&sentinelpassword=spass")
	opts := uriMustGetRedisOptions(uri).Failover()

	if opts.SentinelUsername != "suser" {
		t.Fail()
	}
}

func TestRedisSentinelPasswordOpt(t *testing.T) {
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
