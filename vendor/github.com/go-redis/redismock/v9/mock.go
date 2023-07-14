package redismock

import (
	"context"
	"fmt"
	"net"
	"reflect"
	"regexp"
	"strings"
	"time"

	"github.com/redis/go-redis/v9"
)

type mock struct {
	ctx context.Context

	parent *mock

	factory  redis.Cmdable
	client   redis.Cmdable
	expected []expectation

	strictOrder bool

	expectRegexp bool
	expectCustom CustomMatch

	clientType redisClientType
}

type redisClientType int

const (
	redisClient redisClientType = iota + 1
	redisCluster
)

func NewClientMock() (*redis.Client, ClientMock) {
	m := newMock(redisClient)
	return m.client.(*redis.Client), m
}

func NewClusterMock() (*redis.ClusterClient, ClusterClientMock) {
	m := newMock(redisCluster)
	return m.client.(*redis.ClusterClient), m
}

func newMock(typ redisClientType) *mock {
	m := &mock{
		ctx:        context.Background(),
		clientType: typ,
	}

	// MaxRetries/MaxRedirects set -2, avoid executing commands on the redis server
	switch typ {
	case redisClient:
		opt := &redis.Options{MaxRetries: -2}
		factory := redis.NewClient(opt)
		client := redis.NewClient(opt)
		factory.AddHook(nilHook{})
		client.AddHook(redisClientHook{fn: m.process})

		m.factory = factory
		m.client = client
	case redisCluster:
		opt := &redis.ClusterOptions{MaxRedirects: -2}
		factory := redis.NewClusterClient(opt)
		clusterClient := redis.NewClusterClient(opt)
		factory.AddHook(nilHook{})
		clusterClient.AddHook(redisClientHook{fn: m.process})

		m.factory = factory
		m.client = clusterClient
	}
	m.strictOrder = true

	return m
}

//------------------------------------------------------------------

type redisClientHook struct {
	returnErr error
	fn        func(cmd redis.Cmder) error
}

func (redisClientHook) DialHook(hook redis.DialHook) redis.DialHook {
	return hook
}

func (h redisClientHook) ProcessHook(_ redis.ProcessHook) redis.ProcessHook {
	return func(ctx context.Context, cmd redis.Cmder) error {
		err := h.fn(cmd)
		if h.returnErr != nil && (err == nil || cmd.Err() == nil) {
			err = h.returnErr
		}
		return err
	}
}

func (h redisClientHook) ProcessPipelineHook(_ redis.ProcessPipelineHook) redis.ProcessPipelineHook {
	return func(ctx context.Context, cmds []redis.Cmder) error {
		for _, cmd := range cmds {
			err := h.fn(cmd)
			if h.returnErr != nil && (err == nil || cmd.Err() == nil) {
				err = h.returnErr
			}
			if err != nil {
				return err
			}
		}
		return nil
	}
}

type nilHook struct{}

func (nilHook) DialHook(_ redis.DialHook) redis.DialHook {
	return func(_ context.Context, _, _ string) (net.Conn, error) {
		return &net.TCPConn{}, nil
	}
}

func (h nilHook) ProcessHook(_ redis.ProcessHook) redis.ProcessHook {
	return func(_ context.Context, _ redis.Cmder) error {
		return nil
	}
}

func (h nilHook) ProcessPipelineHook(_ redis.ProcessPipelineHook) redis.ProcessPipelineHook {
	return func(_ context.Context, _ []redis.Cmder) error {
		return nil
	}
}

//----------------------------------

func (m *mock) process(cmd redis.Cmder) (err error) {
	var miss int
	var expect expectation = nil

	for _, e := range m.expected {
		e.lock()

		// not available, has been matched
		if !e.usable() {
			e.unlock()
			miss++
			continue
		}

		err = m.match(e, cmd)

		// matched
		if err == nil {
			expect = e
			break
		}

		// strict order of command execution
		if m.strictOrder {
			e.unlock()
			cmd.SetErr(err)
			return err
		}
		e.unlock()
	}

	if expect == nil {
		msg := "call to cmd '%+v' was not expected"
		if miss == len(m.expected) {
			msg = "all expectations were already fulfilled, " + msg
		}
		err = fmt.Errorf(msg, cmd.Args())
		cmd.SetErr(err)
		return err
	}

	defer expect.unlock()

	expect.trigger()

	// write error
	if err = expect.error(); err != nil {
		cmd.SetErr(err)
		return err
	}

	// write redis.Nil
	if expect.isRedisNil() {
		err = redis.Nil
		cmd.SetErr(err)
		return err
	}

	// if you do not set error or redis.Nil, must set val
	if !expect.isSetVal() {
		err = fmt.Errorf("cmd(%s), return value is required", expect.name())
		cmd.SetErr(err)
		return err
	}

	cmd.SetErr(nil)
	expect.inflow(cmd)

	return nil
}

func (m *mock) match(expect expectation, cmd redis.Cmder) error {
	expectArgs := expect.args()
	cmdArgs := cmd.Args()

	if len(expectArgs) != len(cmdArgs) {
		return fmt.Errorf("parameters do not match, expectation '%+v', but call to cmd '%+v'", expectArgs, cmdArgs)
	}

	if expect.name() != cmd.Name() {
		return fmt.Errorf("command not match, expectation '%s', but call to cmd '%s'", expect.name(), cmd.Name())
	}

	// custom func match
	if fn := expect.custom(); fn != nil {
		return fn(expectArgs, cmdArgs)
	}

	isMapArgs := m.mapArgs(cmd.Name(), &cmdArgs)
	if isMapArgs {
		m.mapArgs(expect.name(), &expectArgs)
	}

	for i := 0; i < len(expectArgs); i++ {
		// is map?
		if isMapArgs {
			expectMapArgs, expectOK := expectArgs[i].(map[string]interface{})
			cmdMapArgs, cmdOK := cmdArgs[i].(map[string]interface{})
			if expectOK && cmdOK {
				// there may be the same key
				if len(expectMapArgs) != len(cmdMapArgs) {
					return fmt.Errorf("wrong number of arguments, expectation regular: '%+v', but gave: '%+v'",
						expectArgs, cmdArgs)
				}
				for expectKey, expectMapVal := range expectMapArgs {
					cmdMapVal, ok := cmdMapArgs[expectKey]
					if !ok {
						return fmt.Errorf("missing command(%s) parameters: %s", expect.name(), expectKey)
					}
					if err := m.compare(expect.regexp(), expectMapVal, cmdMapVal); err != nil {
						return err
					}
				}
				continue
			}
		}
		if err := m.compare(expect.regexp(), expectArgs[i], cmdArgs[i]); err != nil {
			return err
		}
	}

	return nil
}

func (m *mock) compare(isRegexp bool, expect, cmd interface{}) error {
	expr, ok := expect.(string)
	if isRegexp && ok {
		cmdValue := fmt.Sprint(cmd)
		re, err := regexp.Compile(expr)
		if err != nil {
			return err
		}
		if !re.MatchString(cmdValue) {
			return fmt.Errorf("args not match, expectation regular: '%s', but gave: '%s'", expr, cmdValue)
		}
	} else if !reflect.DeepEqual(expect, cmd) {
		return fmt.Errorf("args not `DeepEqual`, expectation: '%+v', but gave: '%+v'", expect, cmd)
	}
	return nil
}

// using map in command leads to disorder, change the command parameter to map[string]interface{}
// for example:
//
//	[mset key1 value1 key2 value2] => [mset map[string]interface{}{"key1": "value1", "key2": "value2"}]
//
// return bool, is it handled
func (m *mock) mapArgs(cmd string, cmdArgs *[]interface{}) bool {
	var cut int
	cmd = strings.ToLower(cmd)
	switch cmd {
	case "mset", "msetnx":
		// 1
		cut = 1
	case "hset", "hmset":
		// 2
		cut = 2
	case "eval", "evalsha":
		// more, i guess nobody uses it (eval/evalsha), miss
		return false
	default:
		return false
	}

	if n := len(*cmdArgs); n <= cut || (n > (cut+1) && (n-cut)%2 != 0) {
		return false
	}

	mapArgs := make(map[string]interface{})
	args := (*cmdArgs)[cut:]
	switch v := args[0].(type) {
	//[]string and map[string]interface{}, types will not appear normally
	case []string:
		if len(v)%2 != 0 {
			return false
		}
		for i := 0; i < len(v); i += 2 {
			mapArgs[v[i]] = v[i+1]
		}
	case map[string]interface{}:
		if len(v) > 0 {
			mapArgs = v
		}
	default:
		for i := 0; i < len(args); i += 2 {
			mapArgs[fmt.Sprint(args[i])] = args[i+1]
		}
	}

	if len(mapArgs) == 0 {
		return false
	}

	newCmd := make([]interface{}, cut, cut+1)
	copy(newCmd[:cut], (*cmdArgs)[:cut])
	newCmd = append(newCmd, mapArgs)
	*cmdArgs = newCmd
	return true
}

func (m *mock) pushExpect(e expectation) {
	if m.expectRegexp {
		e.setRegexpMatch()
	}
	if m.expectCustom != nil {
		e.setCustomMatch(m.expectCustom)
	}
	if m.parent != nil {
		m.parent.pushExpect(e)
		return
	}
	m.expected = append(m.expected, e)
}

func (m *mock) ClearExpect() {
	if m.parent != nil {
		m.parent.ClearExpect()
		return
	}
	m.expected = nil
}

func (m *mock) Regexp() *mock {
	if m.parent != nil {
		return m.parent.Regexp()
	}
	clone := *m
	clone.parent = m
	clone.expectRegexp = true

	return &clone
}

func (m *mock) CustomMatch(fn CustomMatch) *mock {
	if m.parent != nil {
		return m.parent.CustomMatch(fn)
	}
	clone := *m
	clone.parent = m
	clone.expectCustom = fn

	return &clone
}

func (m *mock) ExpectationsWereMet() error {
	if m.parent != nil {
		return m.ExpectationsWereMet()
	}
	for _, e := range m.expected {
		e.lock()
		usable := e.usable()
		e.unlock()

		if usable {
			return fmt.Errorf("there is a remaining expectation which was not matched: %+v", e.args())
		}
	}
	return nil
}

func (m *mock) MatchExpectationsInOrder(b bool) {
	if m.parent != nil {
		m.MatchExpectationsInOrder(b)
		return
	}
	m.strictOrder = b
}

// -----------------------------------------------------

func (m *mock) ExpectTxPipeline() {
	e := &ExpectedStatus{}
	e.cmd = redis.NewStatusCmd(m.ctx, "multi")
	e.SetVal("OK")
	m.pushExpect(e)
}

func (m *mock) ExpectTxPipelineExec() *ExpectedSlice {
	e := &ExpectedSlice{}
	e.cmd = redis.NewSliceCmd(m.ctx, "exec")
	e.SetVal(nil)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectWatch(keys ...string) *ExpectedError {
	e := &ExpectedError{}
	args := make([]interface{}, 1+len(keys))
	args[0] = "watch"
	for i, key := range keys {
		args[1+i] = key
	}
	e.cmd = redis.NewStatusCmd(m.ctx, args...)
	e.setVal = true
	m.pushExpect(e)
	return e
}

// ------------------------------------------------

func (m *mock) ExpectDo(args ...interface{}) *ExpectedCmd {
	e := &ExpectedCmd{}

	switch m.clientType {
	case redisClient:
		e.cmd = m.factory.(*redis.Client).Do(m.ctx, args...)
	case redisCluster:
		e.cmd = m.factory.(*redis.ClusterClient).Do(m.ctx, args...)
	default:
		panic("ExpectDo: unsupported client type")
	}

	m.pushExpect(e)
	return e
}

func (m *mock) ExpectCommand() *ExpectedCommandsInfo {
	e := &ExpectedCommandsInfo{}
	e.cmd = m.factory.Command(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectCommandList(filter *redis.FilterBy) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.CommandList(m.ctx, filter)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectCommandGetKeys(commands ...interface{}) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.CommandGetKeys(m.ctx, commands...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectCommandGetKeysAndFlags(commands ...interface{}) *ExpectedKeyFlags {
	e := &ExpectedKeyFlags{}
	e.cmd = m.factory.CommandGetKeysAndFlags(m.ctx, commands...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientGetName() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.ClientGetName(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectEcho(message interface{}) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.Echo(m.ctx, message)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPing() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Ping(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectQuit() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Quit(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectDel(keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Del(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectUnlink(keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Unlink(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectDump(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.Dump(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectExists(keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Exists(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectExpire(key string, expiration time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.Expire(m.ctx, key, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectExpireAt(key string, tm time.Time) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.ExpireAt(m.ctx, key, tm)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectExpireTime(key string) *ExpectedDuration {
	e := &ExpectedDuration{}
	e.cmd = m.factory.ExpireTime(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectExpireNX(key string, expiration time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.ExpireNX(m.ctx, key, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectExpireXX(key string, expiration time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.ExpireXX(m.ctx, key, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectExpireGT(key string, expiration time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.ExpireGT(m.ctx, key, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectExpireLT(key string, expiration time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.ExpireLT(m.ctx, key, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectKeys(pattern string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.Keys(m.ctx, pattern)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectMigrate(host, port, key string, db int, timeout time.Duration) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Migrate(m.ctx, host, port, key, db, timeout)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectMove(key string, db int) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.Move(m.ctx, key, db)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectObjectRefCount(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ObjectRefCount(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectObjectEncoding(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.ObjectEncoding(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectObjectIdleTime(key string) *ExpectedDuration {
	e := &ExpectedDuration{}
	e.cmd = m.factory.ObjectIdleTime(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPersist(key string) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.Persist(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPExpire(key string, expiration time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.PExpire(m.ctx, key, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPExpireAt(key string, tm time.Time) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.PExpireAt(m.ctx, key, tm)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPExpireTime(key string) *ExpectedDuration {
	e := &ExpectedDuration{}
	e.cmd = m.factory.PExpireTime(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPTTL(key string) *ExpectedDuration {
	e := &ExpectedDuration{}
	e.cmd = m.factory.PTTL(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRandomKey() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.RandomKey(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRename(key, newkey string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Rename(m.ctx, key, newkey)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRenameNX(key, newkey string) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.RenameNX(m.ctx, key, newkey)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRestore(key string, ttl time.Duration, value string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Restore(m.ctx, key, ttl, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRestoreReplace(key string, ttl time.Duration, value string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.RestoreReplace(m.ctx, key, ttl, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSort(key string, sort *redis.Sort) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.Sort(m.ctx, key, sort)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSortRO(key string, sort *redis.Sort) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.SortRO(m.ctx, key, sort)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSortStore(key, store string, sort *redis.Sort) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SortStore(m.ctx, key, store, sort)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSortInterfaces(key string, sort *redis.Sort) *ExpectedSlice {
	e := &ExpectedSlice{}
	e.cmd = m.factory.SortInterfaces(m.ctx, key, sort)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectTouch(keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Touch(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectTTL(key string) *ExpectedDuration {
	e := &ExpectedDuration{}
	e.cmd = m.factory.TTL(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectType(key string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Type(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectAppend(key, value string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Append(m.ctx, key, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectDecr(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Decr(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectDecrBy(key string, decrement int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.DecrBy(m.ctx, key, decrement)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGet(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.Get(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGetRange(key string, start, end int64) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.GetRange(m.ctx, key, start, end)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGetSet(key string, value interface{}) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.GetSet(m.ctx, key, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGetEx(key string, expiration time.Duration) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.GetEx(m.ctx, key, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGetDel(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.GetDel(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectIncr(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Incr(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectIncrBy(key string, value int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.IncrBy(m.ctx, key, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectIncrByFloat(key string, value float64) *ExpectedFloat {
	e := &ExpectedFloat{}
	e.cmd = m.factory.IncrByFloat(m.ctx, key, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectMGet(keys ...string) *ExpectedSlice {
	e := &ExpectedSlice{}
	e.cmd = m.factory.MGet(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectMSet(values ...interface{}) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.MSet(m.ctx, values...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectMSetNX(values ...interface{}) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.MSetNX(m.ctx, values...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSet(key string, value interface{}, expiration time.Duration) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Set(m.ctx, key, value, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSetArgs(key string, value interface{}, a redis.SetArgs) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.SetArgs(m.ctx, key, value, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSetEx(key string, value interface{}, expiration time.Duration) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.SetEx(m.ctx, key, value, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSetNX(key string, value interface{}, expiration time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.SetNX(m.ctx, key, value, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSetXX(key string, value interface{}, expiration time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.SetXX(m.ctx, key, value, expiration)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSetRange(key string, offset int64, value string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SetRange(m.ctx, key, offset, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectStrLen(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.StrLen(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectCopy(sourceKey string, destKey string, db int, replace bool) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Copy(m.ctx, sourceKey, destKey, db, replace)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGetBit(key string, offset int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.GetBit(m.ctx, key, offset)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSetBit(key string, offset int64, value int) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SetBit(m.ctx, key, offset, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBitCount(key string, bitCount *redis.BitCount) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.BitCount(m.ctx, key, bitCount)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBitOpAnd(destKey string, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.BitOpAnd(m.ctx, destKey, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBitOpOr(destKey string, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.BitOpOr(m.ctx, destKey, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBitOpXor(destKey string, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.BitOpXor(m.ctx, destKey, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBitOpNot(destKey string, key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.BitOpNot(m.ctx, destKey, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBitPos(key string, bit int64, pos ...int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.BitPos(m.ctx, key, bit, pos...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBitPosSpan(key string, bit int8, start, end int64, span string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.BitPosSpan(m.ctx, key, bit, start, end, span)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBitField(key string, args ...interface{}) *ExpectedIntSlice {
	e := &ExpectedIntSlice{}
	e.cmd = m.factory.BitField(m.ctx, key, args...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectScan(cursor uint64, match string, count int64) *ExpectedScan {
	e := &ExpectedScan{}
	e.cmd = m.factory.Scan(m.ctx, cursor, match, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectScanType(cursor uint64, match string, count int64, keyType string) *ExpectedScan {
	e := &ExpectedScan{}
	e.cmd = m.factory.ScanType(m.ctx, cursor, match, count, keyType)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSScan(key string, cursor uint64, match string, count int64) *ExpectedScan {
	e := &ExpectedScan{}
	e.cmd = m.factory.SScan(m.ctx, key, cursor, match, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHScan(key string, cursor uint64, match string, count int64) *ExpectedScan {
	e := &ExpectedScan{}
	e.cmd = m.factory.HScan(m.ctx, key, cursor, match, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZScan(key string, cursor uint64, match string, count int64) *ExpectedScan {
	e := &ExpectedScan{}
	e.cmd = m.factory.ZScan(m.ctx, key, cursor, match, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHDel(key string, fields ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.HDel(m.ctx, key, fields...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHExists(key, field string) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.HExists(m.ctx, key, field)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHGet(key, field string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.HGet(m.ctx, key, field)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHGetAll(key string) *ExpectedMapStringString {
	e := &ExpectedMapStringString{}
	e.cmd = m.factory.HGetAll(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHIncrBy(key, field string, incr int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.HIncrBy(m.ctx, key, field, incr)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHIncrByFloat(key, field string, incr float64) *ExpectedFloat {
	e := &ExpectedFloat{}
	e.cmd = m.factory.HIncrByFloat(m.ctx, key, field, incr)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHKeys(key string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.HKeys(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHLen(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.HLen(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHMGet(key string, fields ...string) *ExpectedSlice {
	e := &ExpectedSlice{}
	e.cmd = m.factory.HMGet(m.ctx, key, fields...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHSet(key string, values ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.HSet(m.ctx, key, values...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHMSet(key string, values ...interface{}) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.HMSet(m.ctx, key, values...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHSetNX(key, field string, value interface{}) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.HSetNX(m.ctx, key, field, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHVals(key string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.HVals(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHRandField(key string, count int) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.HRandField(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectHRandFieldWithValues(key string, count int) *ExpectedKeyValueSlice {
	e := &ExpectedKeyValueSlice{}
	e.cmd = m.factory.HRandFieldWithValues(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBLPop(timeout time.Duration, keys ...string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.BLPop(m.ctx, timeout, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBLMPop(timeout time.Duration, direction string, count int64, keys ...string) *ExpectedKeyValues {
	e := &ExpectedKeyValues{}
	e.cmd = m.factory.BLMPop(m.ctx, timeout, direction, count, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBRPop(timeout time.Duration, keys ...string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.BRPop(m.ctx, timeout, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBRPopLPush(source, destination string, timeout time.Duration) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.BRPopLPush(m.ctx, source, destination, timeout)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLCS(q *redis.LCSQuery) *ExpectedLCS {
	e := &ExpectedLCS{}
	e.cmd = m.factory.LCS(m.ctx, q)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLIndex(key string, index int64) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.LIndex(m.ctx, key, index)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLInsert(key, op string, pivot, value interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LInsert(m.ctx, key, op, pivot, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLInsertBefore(key string, pivot, value interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LInsertBefore(m.ctx, key, pivot, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLInsertAfter(key string, pivot, value interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LInsertAfter(m.ctx, key, pivot, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLLen(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LLen(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLPop(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.LPop(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLPopCount(key string, count int) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.LPopCount(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLMPop(direction string, count int64, keys ...string) *ExpectedKeyValues {
	e := &ExpectedKeyValues{}
	e.cmd = m.factory.LMPop(m.ctx, direction, count, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLPos(key string, value string, args redis.LPosArgs) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LPos(m.ctx, key, value, args)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLPosCount(key string, value string, count int64, args redis.LPosArgs) *ExpectedIntSlice {
	e := &ExpectedIntSlice{}
	e.cmd = m.factory.LPosCount(m.ctx, key, value, count, args)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLPush(key string, values ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LPush(m.ctx, key, values...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLPushX(key string, values ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LPushX(m.ctx, key, values...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLRange(key string, start, stop int64) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.LRange(m.ctx, key, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLRem(key string, count int64, value interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LRem(m.ctx, key, count, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLSet(key string, index int64, value interface{}) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.LSet(m.ctx, key, index, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLTrim(key string, start, stop int64) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.LTrim(m.ctx, key, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRPop(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.RPop(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRPopCount(key string, count int) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.RPopCount(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRPopLPush(source, destination string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.RPopLPush(m.ctx, source, destination)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRPush(key string, values ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.RPush(m.ctx, key, values...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectRPushX(key string, values ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.RPushX(m.ctx, key, values...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLMove(source, destination, srcpos, destpos string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.LMove(m.ctx, source, destination, srcpos, destpos)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBLMove(source, destination, srcpos, destpos string, timeout time.Duration) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.BLMove(m.ctx, source, destination, srcpos, destpos, timeout)
	m.pushExpect(e)
	return e
}

// --------------------------------------------------------------

func (m *mock) ExpectSAdd(key string, members ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SAdd(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSCard(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SCard(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSDiff(keys ...string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.SDiff(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSDiffStore(destination string, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SDiffStore(m.ctx, destination, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSInter(keys ...string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.SInter(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSInterCard(limit int64, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SInterCard(m.ctx, limit, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSInterStore(destination string, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SInterStore(m.ctx, destination, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSIsMember(key string, member interface{}) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.SIsMember(m.ctx, key, member)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSMIsMember(key string, members ...interface{}) *ExpectedBoolSlice {
	e := &ExpectedBoolSlice{}
	e.cmd = m.factory.SMIsMember(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSMembers(key string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.SMembers(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSMembersMap(key string) *ExpectedStringStructMap {
	e := &ExpectedStringStructMap{}
	e.cmd = m.factory.SMembersMap(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSMove(source, destination string, member interface{}) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.SMove(m.ctx, source, destination, member)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSPop(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.SPop(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSPopN(key string, count int64) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.SPopN(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSRandMember(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.SRandMember(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSRandMemberN(key string, count int64) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.SRandMemberN(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSRem(key string, members ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SRem(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSUnion(keys ...string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.SUnion(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSUnionStore(destination string, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SUnionStore(m.ctx, destination, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXAdd(a *redis.XAddArgs) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.XAdd(m.ctx, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXDel(stream string, ids ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XDel(m.ctx, stream, ids...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXLen(stream string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XLen(m.ctx, stream)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXRange(stream, start, stop string) *ExpectedXMessageSlice {
	e := &ExpectedXMessageSlice{}
	e.cmd = m.factory.XRange(m.ctx, stream, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXRangeN(stream, start, stop string, count int64) *ExpectedXMessageSlice {
	e := &ExpectedXMessageSlice{}
	e.cmd = m.factory.XRangeN(m.ctx, stream, start, stop, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXRevRange(stream string, start, stop string) *ExpectedXMessageSlice {
	e := &ExpectedXMessageSlice{}
	e.cmd = m.factory.XRevRange(m.ctx, stream, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXRevRangeN(stream string, start, stop string, count int64) *ExpectedXMessageSlice {
	e := &ExpectedXMessageSlice{}
	e.cmd = m.factory.XRevRangeN(m.ctx, stream, start, stop, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXRead(a *redis.XReadArgs) *ExpectedXStreamSlice {
	e := &ExpectedXStreamSlice{}
	e.cmd = m.factory.XRead(m.ctx, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXReadStreams(streams ...string) *ExpectedXStreamSlice {
	e := &ExpectedXStreamSlice{}
	e.cmd = m.factory.XReadStreams(m.ctx, streams...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXGroupCreate(stream, group, start string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.XGroupCreate(m.ctx, stream, group, start)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXGroupCreateMkStream(stream, group, start string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.XGroupCreateMkStream(m.ctx, stream, group, start)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXGroupSetID(stream, group, start string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.XGroupSetID(m.ctx, stream, group, start)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXGroupDestroy(stream, group string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XGroupDestroy(m.ctx, stream, group)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXGroupCreateConsumer(stream, group, consumer string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XGroupCreateConsumer(m.ctx, stream, group, consumer)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXGroupDelConsumer(stream, group, consumer string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XGroupDelConsumer(m.ctx, stream, group, consumer)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXReadGroup(a *redis.XReadGroupArgs) *ExpectedXStreamSlice {
	e := &ExpectedXStreamSlice{}
	e.cmd = m.factory.XReadGroup(m.ctx, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXAck(stream, group string, ids ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XAck(m.ctx, stream, group, ids...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXPending(stream, group string) *ExpectedXPending {
	e := &ExpectedXPending{}
	e.cmd = m.factory.XPending(m.ctx, stream, group)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXPendingExt(a *redis.XPendingExtArgs) *ExpectedXPendingExt {
	e := &ExpectedXPendingExt{}
	e.cmd = m.factory.XPendingExt(m.ctx, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXClaim(a *redis.XClaimArgs) *ExpectedXMessageSlice {
	e := &ExpectedXMessageSlice{}
	e.cmd = m.factory.XClaim(m.ctx, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXClaimJustID(a *redis.XClaimArgs) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.XClaimJustID(m.ctx, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXAutoClaim(a *redis.XAutoClaimArgs) *ExpectedXAutoClaim {
	e := &ExpectedXAutoClaim{}
	e.cmd = m.factory.XAutoClaim(m.ctx, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXAutoClaimJustID(a *redis.XAutoClaimArgs) *ExpectedXAutoClaimJustID {
	e := &ExpectedXAutoClaimJustID{}
	e.cmd = m.factory.XAutoClaimJustID(m.ctx, a)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXTrimMaxLen(key string, maxLen int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XTrimMaxLen(m.ctx, key, maxLen)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXTrimMaxLenApprox(key string, maxLen, limit int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XTrimMaxLenApprox(m.ctx, key, maxLen, limit)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXTrimMinID(key string, minID string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XTrimMinID(m.ctx, key, minID)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXTrimMinIDApprox(key string, minID string, limit int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.XTrimMinIDApprox(m.ctx, key, minID, limit)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXInfoGroups(key string) *ExpectedXInfoGroups {
	e := &ExpectedXInfoGroups{}
	e.cmd = m.factory.XInfoGroups(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXInfoStream(key string) *ExpectedXInfoStream {
	e := &ExpectedXInfoStream{}
	e.cmd = m.factory.XInfoStream(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXInfoStreamFull(key string, count int) *ExpectedXInfoStreamFull {
	e := &ExpectedXInfoStreamFull{}
	e.cmd = m.factory.XInfoStreamFull(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectXInfoConsumers(key string, group string) *ExpectedXInfoConsumers {
	e := &ExpectedXInfoConsumers{}
	e.cmd = m.factory.XInfoConsumers(m.ctx, key, group)
	m.pushExpect(e)
	return e
}

// ------------------------------------------------------------------------------------------

func (m *mock) ExpectBZPopMax(timeout time.Duration, keys ...string) *ExpectedZWithKey {
	e := &ExpectedZWithKey{}
	e.cmd = m.factory.BZPopMax(m.ctx, timeout, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBZPopMin(timeout time.Duration, keys ...string) *ExpectedZWithKey {
	e := &ExpectedZWithKey{}
	e.cmd = m.factory.BZPopMin(m.ctx, timeout, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBZMPop(timeout time.Duration, order string, count int64, keys ...string) *ExpectedZSliceWithKey {
	e := &ExpectedZSliceWithKey{}
	e.cmd = m.factory.BZMPop(m.ctx, timeout, order, count, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZAdd(key string, members ...redis.Z) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZAdd(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZAddLT(key string, members ...redis.Z) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZAddLT(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZAddGT(key string, members ...redis.Z) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZAddGT(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZAddNX(key string, members ...redis.Z) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZAddNX(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZAddXX(key string, members ...redis.Z) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZAddXX(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZAddArgs(key string, args redis.ZAddArgs) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZAddArgs(m.ctx, key, args)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZAddArgsIncr(key string, args redis.ZAddArgs) *ExpectedFloat {
	e := &ExpectedFloat{}
	e.cmd = m.factory.ZAddArgsIncr(m.ctx, key, args)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZCard(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZCard(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZCount(key, min, max string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZCount(m.ctx, key, min, max)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZLexCount(key, min, max string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZLexCount(m.ctx, key, min, max)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZIncrBy(key string, increment float64, member string) *ExpectedFloat {
	e := &ExpectedFloat{}
	e.cmd = m.factory.ZIncrBy(m.ctx, key, increment, member)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZInter(store *redis.ZStore) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZInter(m.ctx, store)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZInterWithScores(store *redis.ZStore) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZInterWithScores(m.ctx, store)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZInterCard(limit int64, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZInterCard(m.ctx, limit, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZInterStore(destination string, store *redis.ZStore) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZInterStore(m.ctx, destination, store)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZMPop(order string, count int64, keys ...string) *ExpectedZSliceWithKey {
	e := &ExpectedZSliceWithKey{}
	e.cmd = m.factory.ZMPop(m.ctx, order, count, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZMScore(key string, members ...string) *ExpectedFloatSlice {
	e := &ExpectedFloatSlice{}
	e.cmd = m.factory.ZMScore(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZPopMax(key string, count ...int64) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZPopMax(m.ctx, key, count...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZPopMin(key string, count ...int64) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZPopMin(m.ctx, key, count...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRange(key string, start, stop int64) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZRange(m.ctx, key, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRangeWithScores(key string, start, stop int64) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZRangeWithScores(m.ctx, key, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRangeByScore(key string, opt *redis.ZRangeBy) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZRangeByScore(m.ctx, key, opt)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRangeByLex(key string, opt *redis.ZRangeBy) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZRangeByLex(m.ctx, key, opt)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRangeByScoreWithScores(key string, opt *redis.ZRangeBy) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZRangeByScoreWithScores(m.ctx, key, opt)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRangeArgs(z redis.ZRangeArgs) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZRangeArgs(m.ctx, z)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRangeArgsWithScores(z redis.ZRangeArgs) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZRangeArgsWithScores(m.ctx, z)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRangeStore(dst string, z redis.ZRangeArgs) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZRangeStore(m.ctx, dst, z)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRank(key, member string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZRank(m.ctx, key, member)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRem(key string, members ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZRem(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRemRangeByRank(key string, start, stop int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZRemRangeByRank(m.ctx, key, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRemRangeByScore(key, min, max string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZRemRangeByScore(m.ctx, key, min, max)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRemRangeByLex(key, min, max string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZRemRangeByLex(m.ctx, key, min, max)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRevRange(key string, start, stop int64) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZRevRange(m.ctx, key, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRevRangeWithScores(key string, start, stop int64) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZRevRangeWithScores(m.ctx, key, start, stop)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRevRangeByScore(key string, opt *redis.ZRangeBy) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZRevRangeByScore(m.ctx, key, opt)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRevRangeByLex(key string, opt *redis.ZRangeBy) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZRevRangeByLex(m.ctx, key, opt)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRevRangeByScoreWithScores(key string, opt *redis.ZRangeBy) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZRevRangeByScoreWithScores(m.ctx, key, opt)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRevRank(key, member string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZRevRank(m.ctx, key, member)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZScore(key, member string) *ExpectedFloat {
	e := &ExpectedFloat{}
	e.cmd = m.factory.ZScore(m.ctx, key, member)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZUnionStore(dest string, store *redis.ZStore) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZUnionStore(m.ctx, dest, store)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRandMember(key string, count int) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZRandMember(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZRandMemberWithScores(key string, count int) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZRandMemberWithScores(m.ctx, key, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZUnion(store redis.ZStore) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZUnion(m.ctx, store)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZUnionWithScores(store redis.ZStore) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZUnionWithScores(m.ctx, store)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZDiff(keys ...string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ZDiff(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZDiffWithScores(keys ...string) *ExpectedZSlice {
	e := &ExpectedZSlice{}
	e.cmd = m.factory.ZDiffWithScores(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectZDiffStore(destination string, keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ZDiffStore(m.ctx, destination, keys...)
	m.pushExpect(e)
	return e
}

// ----------------------------------------------------------------------------

func (m *mock) ExpectPFAdd(key string, els ...interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.PFAdd(m.ctx, key, els...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPFCount(keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.PFCount(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPFMerge(dest string, keys ...string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.PFMerge(m.ctx, dest, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBgRewriteAOF() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.BgRewriteAOF(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectBgSave() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.BgSave(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientKill(ipPort string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClientKill(m.ctx, ipPort)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientKillByFilter(keys ...string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ClientKillByFilter(m.ctx, keys...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientList() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.ClientList(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientPause(dur time.Duration) *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.ClientPause(m.ctx, dur)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientUnpause() *ExpectedBool {
	e := &ExpectedBool{}
	e.cmd = m.factory.ClientUnpause(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientID() *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ClientID(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientUnblock(id int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ClientUnblock(m.ctx, id)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClientUnblockWithError(id int64) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ClientUnblockWithError(m.ctx, id)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectConfigGet(parameter string) *ExpectedMapStringString {
	e := &ExpectedMapStringString{}
	e.cmd = m.factory.ConfigGet(m.ctx, parameter)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectConfigResetStat() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ConfigResetStat(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectConfigSet(parameter, value string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ConfigSet(m.ctx, parameter, value)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectConfigRewrite() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ConfigRewrite(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectDBSize() *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.DBSize(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFlushAll() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.FlushAll(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFlushAllAsync() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.FlushAllAsync(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFlushDB() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.FlushDB(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFlushDBAsync() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.FlushDBAsync(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectInfo(section ...string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.Info(m.ctx, section...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectLastSave() *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.LastSave(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSave() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Save(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectShutdown() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.Shutdown(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectShutdownSave() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ShutdownSave(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectShutdownNoSave() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ShutdownNoSave(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSlaveOf(host, port string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.SlaveOf(m.ctx, host, port)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSlowLogGet(num int64) *ExpectedSlowLog {
	e := &ExpectedSlowLog{}
	e.cmd = m.factory.SlowLogGet(m.ctx, num)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectTime() *ExpectedTime {
	e := &ExpectedTime{}
	e.cmd = m.factory.Time(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectDebugObject(key string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.DebugObject(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectReadOnly() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ReadOnly(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectReadWrite() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ReadWrite(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectMemoryUsage(key string, samples ...int) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.MemoryUsage(m.ctx, key, samples...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectEval(script string, keys []string, args ...interface{}) *ExpectedCmd {
	e := &ExpectedCmd{}
	e.cmd = m.factory.Eval(m.ctx, script, keys, args...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectEvalSha(sha1 string, keys []string, args ...interface{}) *ExpectedCmd {
	e := &ExpectedCmd{}
	e.cmd = m.factory.EvalSha(m.ctx, sha1, keys, args...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectEvalRO(script string, keys []string, args ...interface{}) *ExpectedCmd {
	e := &ExpectedCmd{}
	e.cmd = m.factory.EvalRO(m.ctx, script, keys, args...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectEvalShaRO(sha1 string, keys []string, args ...interface{}) *ExpectedCmd {
	e := &ExpectedCmd{}
	e.cmd = m.factory.EvalShaRO(m.ctx, sha1, keys, args...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectScriptExists(hashes ...string) *ExpectedBoolSlice {
	e := &ExpectedBoolSlice{}
	e.cmd = m.factory.ScriptExists(m.ctx, hashes...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectScriptFlush() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ScriptFlush(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectScriptKill() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ScriptKill(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectScriptLoad(script string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.ScriptLoad(m.ctx, script)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPublish(channel string, message interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.Publish(m.ctx, channel, message)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectSPublish(channel string, message interface{}) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.SPublish(m.ctx, channel, message)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPubSubChannels(pattern string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.PubSubChannels(m.ctx, pattern)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPubSubNumSub(channels ...string) *ExpectedMapStringInt {
	e := &ExpectedMapStringInt{}
	e.cmd = m.factory.PubSubNumSub(m.ctx, channels...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPubSubNumPat() *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.PubSubNumPat(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPubSubShardChannels(pattern string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.PubSubShardChannels(m.ctx, pattern)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectPubSubShardNumSub(channels ...string) *ExpectedMapStringInt {
	e := &ExpectedMapStringInt{}
	e.cmd = m.factory.PubSubShardNumSub(m.ctx, channels...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterSlots() *ExpectedClusterSlots {
	e := &ExpectedClusterSlots{}
	e.cmd = m.factory.ClusterSlots(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterShards() *ExpectedClusterShards {
	e := &ExpectedClusterShards{}
	e.cmd = m.factory.ClusterShards(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterLinks() *ExpectedClusterLinks {
	e := &ExpectedClusterLinks{}
	e.cmd = m.factory.ClusterLinks(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterNodes() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.ClusterNodes(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterMeet(host, port string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterMeet(m.ctx, host, port)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterForget(nodeID string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterForget(m.ctx, nodeID)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterReplicate(nodeID string) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterReplicate(m.ctx, nodeID)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterResetSoft() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterResetSoft(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterResetHard() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterResetHard(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterInfo() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.ClusterInfo(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterKeySlot(key string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ClusterKeySlot(m.ctx, key)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterGetKeysInSlot(slot int, count int) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ClusterGetKeysInSlot(m.ctx, slot, count)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterCountFailureReports(nodeID string) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ClusterCountFailureReports(m.ctx, nodeID)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterCountKeysInSlot(slot int) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.ClusterCountKeysInSlot(m.ctx, slot)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterDelSlots(slots ...int) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterDelSlots(m.ctx, slots...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterDelSlotsRange(min, max int) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterDelSlotsRange(m.ctx, min, max)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterSaveConfig() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterSaveConfig(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterSlaves(nodeID string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.ClusterSlaves(m.ctx, nodeID)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterFailover() *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterFailover(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterAddSlots(slots ...int) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterAddSlots(m.ctx, slots...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectClusterAddSlotsRange(min, max int) *ExpectedStatus {
	e := &ExpectedStatus{}
	e.cmd = m.factory.ClusterAddSlotsRange(m.ctx, min, max)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoAdd(key string, geoLocation ...*redis.GeoLocation) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.GeoAdd(m.ctx, key, geoLocation...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoPos(key string, members ...string) *ExpectedGeoPos {
	e := &ExpectedGeoPos{}
	e.cmd = m.factory.GeoPos(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoRadius(
	key string, longitude, latitude float64, query *redis.GeoRadiusQuery,
) *ExpectedGeoLocation {
	e := &ExpectedGeoLocation{}
	e.cmd = m.factory.GeoRadius(m.ctx, key, longitude, latitude, query)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoRadiusStore(
	key string, longitude, latitude float64, query *redis.GeoRadiusQuery,
) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.GeoRadiusStore(m.ctx, key, longitude, latitude, query)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoRadiusByMember(key, member string, query *redis.GeoRadiusQuery) *ExpectedGeoLocation {
	e := &ExpectedGeoLocation{}
	e.cmd = m.factory.GeoRadiusByMember(m.ctx, key, member, query)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoRadiusByMemberStore(key, member string, query *redis.GeoRadiusQuery) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.GeoRadiusByMemberStore(m.ctx, key, member, query)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoSearch(key string, q *redis.GeoSearchQuery) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.GeoSearch(m.ctx, key, q)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoSearchLocation(key string, q *redis.GeoSearchLocationQuery) *ExpectedGeoSearchLocation {
	e := &ExpectedGeoSearchLocation{}
	e.cmd = m.factory.GeoSearchLocation(m.ctx, key, q)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoSearchStore(key, store string, q *redis.GeoSearchStoreQuery) *ExpectedInt {
	e := &ExpectedInt{}
	e.cmd = m.factory.GeoSearchStore(m.ctx, key, store, q)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoDist(key string, member1, member2, unit string) *ExpectedFloat {
	e := &ExpectedFloat{}
	e.cmd = m.factory.GeoDist(m.ctx, key, member1, member2, unit)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectGeoHash(key string, members ...string) *ExpectedStringSlice {
	e := &ExpectedStringSlice{}
	e.cmd = m.factory.GeoHash(m.ctx, key, members...)
	m.pushExpect(e)
	return e
}

// ----------------------------------------------------------------------------------------------------

func (m *mock) ExpectFunctionLoad(code string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.FunctionLoad(m.ctx, code)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFunctionLoadReplace(code string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.FunctionLoadReplace(m.ctx, code)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFunctionDelete(libName string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.FunctionDelete(m.ctx, libName)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFunctionFlush() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.FunctionFlush(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFunctionFlushAsync() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.FunctionFlushAsync(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFunctionList(q redis.FunctionListQuery) *ExpectedFunctionList {
	e := &ExpectedFunctionList{}
	e.cmd = m.factory.FunctionList(m.ctx, q)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFunctionKill() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.FunctionKill(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFunctionDump() *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.FunctionDump(m.ctx)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFunctionRestore(libDump string) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.FunctionRestore(m.ctx, libDump)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFCall(function string, keys []string, args ...interface{}) *ExpectedCmd {
	e := &ExpectedCmd{}
	e.cmd = m.factory.FCall(m.ctx, function, keys, args...)
	m.pushExpect(e)
	return e
}

func (m *mock) ExpectFCallRo(function string, keys []string, args ...interface{}) *ExpectedCmd {
	e := &ExpectedCmd{}
	e.cmd = m.factory.FCallRo(m.ctx, function, keys, args...)
	m.pushExpect(e)
	return e
}

// ------------------------------------------------------------------------

func (m *mock) ExpectACLDryRun(username string, command ...interface{}) *ExpectedString {
	e := &ExpectedString{}
	e.cmd = m.factory.ACLDryRun(m.ctx, username, command...)
	m.pushExpect(e)
	return e
}
