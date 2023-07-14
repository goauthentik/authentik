# go-env

[![Build Status](https://travis-ci.com/Netflix/go-env.svg?branch=master)](https://travis-ci.com/Netflix/go-env)
[![GoDoc](https://godoc.org/github.com/Netflix/go-env?status.svg)](https://godoc.org/github.com/Netflix/go-env)
[![NetflixOSS Lifecycle](https://img.shields.io/osslifecycle/Netflix/go-expect.svg)]()


Package env provides an `env` struct field tag to marshal and unmarshal environment variables.

## Usage

```go
package main

import (
	"log"
	"time"

	env "github.com/Netflix/go-env"
)

type Environment struct {
	Home string `env:"HOME"`

	Jenkins struct {
		BuildId     *string `env:"BUILD_ID"`
		BuildNumber int     `env:"BUILD_NUMBER"`
		Ci          bool    `env:"CI"`
	}

	Node struct {
		ConfigCache *string `env:"npm_config_cache,NPM_CONFIG_CACHE"`
	}

	Extras env.EnvSet

	Duration      time.Duration `env:"TYPE_DURATION"`
	DefaultValue  string        `env:"MISSING_VAR,default=default_value"`
	RequiredValue string        `env:"IM_REQUIRED,required=true"`
}

func main() {
	var environment Environment
	es, err := env.UnmarshalFromEnviron(&environment)
	if err != nil {
		log.Fatal(err)
	}
	// Remaining environment variables.
	environment.Extras = es

	// ...

	es, err = env.Marshal(environment)
	if err != nil {
		log.Fatal(err)
	}

	home := "/tmp/edgarl"
	cs := env.ChangeSet{
		"HOME":         &home,
		"BUILD_ID":     nil,
		"BUILD_NUMBER": nil,
	}
	es.Apply(cs)

	environment = Environment{}
	err = env.Unmarshal(es, &environment)
	if err != nil {
		log.Fatal(err)
	}

	environment.Extras = es
}
```

## Custom Marshaler/Unmarshaler

There is limited support for dictating how a field should be marshaled or unmarshaled. The following example
shows how you could marshal/unmarshal from JSON

```go
import (
	"encoding/json"
	"fmt"
	"log"
	
    env "github.com/Netflix/go-env"
)

type SomeData struct {
    SomeField int `json:"someField"`
}

func (s *SomeData) UnmarshalEnvironmentValue(data string) error {
    var tmp SomeData
    err := json.Unmarshal([]byte(data), &tmp)
	if err != nil {
		return err
	}
	*s = tmp 
	return nil
}

func (s SomeData) MarshalEnvironmentValue() (string, error) {
	bytes, err := json.Marshal(s)
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

type Config struct {
    SomeData *SomeData `env:"SOME_DATA"`
}

func main() {
	var cfg Config 
	_, err := env.UnmarshalFromEnviron(&cfg)
	if err != nil {
		log.Fatal(err)
	}

    if cfg.SomeData != nil && cfg.SomeData.SomeField == 42 {
        fmt.Println("Got 42!")
    } else {
        fmt.Printf("Got nil or some other value: %v\n", cfg.SomeData)
    }

    es, err = env.Marshal(cfg)
	if err != nil {
		log.Fatal(err)
	}
    fmt.Printf("Got the following: %+v\n", es)
}
```
