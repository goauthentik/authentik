package redismock

import (
	"fmt"
	"reflect"
	"sync"
	"time"
	"unsafe"

	"github.com/redis/go-redis/v9"
)

type baseMock interface {
	// ClearExpect clear whether all queued expectations were met in order
	ClearExpect()

	// Regexp using the regular match command
	Regexp() *mock

	// CustomMatch using custom matching functions
	CustomMatch(fn CustomMatch) *mock

	// ExpectationsWereMet checks whether all queued expectations
	// were met in order. If any of them was not met - an error is returned.
	ExpectationsWereMet() error

	// MatchExpectationsInOrder gives an option whether to match all expectations in the order they were set or not.
	MatchExpectationsInOrder(b bool)

	ExpectDo(args ...interface{}) *ExpectedCmd
	ExpectCommand() *ExpectedCommandsInfo
	ExpectCommandList(filter *redis.FilterBy) *ExpectedStringSlice
	ExpectCommandGetKeys(commands ...interface{}) *ExpectedStringSlice
	ExpectCommandGetKeysAndFlags(commands ...interface{}) *ExpectedKeyFlags
	ExpectClientGetName() *ExpectedString
	ExpectEcho(message interface{}) *ExpectedString
	ExpectPing() *ExpectedStatus
	ExpectQuit() *ExpectedStatus
	ExpectDel(keys ...string) *ExpectedInt
	ExpectUnlink(keys ...string) *ExpectedInt
	ExpectDump(key string) *ExpectedString
	ExpectExists(keys ...string) *ExpectedInt
	ExpectExpire(key string, expiration time.Duration) *ExpectedBool
	ExpectExpireAt(key string, tm time.Time) *ExpectedBool
	ExpectExpireTime(key string) *ExpectedDuration
	ExpectExpireNX(key string, expiration time.Duration) *ExpectedBool
	ExpectExpireXX(key string, expiration time.Duration) *ExpectedBool
	ExpectExpireGT(key string, expiration time.Duration) *ExpectedBool
	ExpectExpireLT(key string, expiration time.Duration) *ExpectedBool
	ExpectKeys(pattern string) *ExpectedStringSlice
	ExpectMigrate(host, port, key string, db int, timeout time.Duration) *ExpectedStatus
	ExpectMove(key string, db int) *ExpectedBool
	ExpectObjectRefCount(key string) *ExpectedInt
	ExpectObjectEncoding(key string) *ExpectedString
	ExpectObjectIdleTime(key string) *ExpectedDuration
	ExpectPersist(key string) *ExpectedBool
	ExpectPExpire(key string, expiration time.Duration) *ExpectedBool
	ExpectPExpireAt(key string, tm time.Time) *ExpectedBool
	ExpectPExpireTime(key string) *ExpectedDuration
	ExpectPTTL(key string) *ExpectedDuration
	ExpectRandomKey() *ExpectedString
	ExpectRename(key, newkey string) *ExpectedStatus
	ExpectRenameNX(key, newkey string) *ExpectedBool
	ExpectRestore(key string, ttl time.Duration, value string) *ExpectedStatus
	ExpectRestoreReplace(key string, ttl time.Duration, value string) *ExpectedStatus
	ExpectSort(key string, sort *redis.Sort) *ExpectedStringSlice
	ExpectSortRO(key string, sort *redis.Sort) *ExpectedStringSlice
	ExpectSortStore(key, store string, sort *redis.Sort) *ExpectedInt
	ExpectSortInterfaces(key string, sort *redis.Sort) *ExpectedSlice
	ExpectTouch(keys ...string) *ExpectedInt
	ExpectTTL(key string) *ExpectedDuration
	ExpectType(key string) *ExpectedStatus
	ExpectAppend(key, value string) *ExpectedInt
	ExpectDecr(key string) *ExpectedInt
	ExpectDecrBy(key string, decrement int64) *ExpectedInt
	ExpectGet(key string) *ExpectedString
	ExpectGetRange(key string, start, end int64) *ExpectedString
	ExpectGetSet(key string, value interface{}) *ExpectedString
	ExpectGetEx(key string, expiration time.Duration) *ExpectedString
	ExpectGetDel(key string) *ExpectedString
	ExpectIncr(key string) *ExpectedInt
	ExpectIncrBy(key string, value int64) *ExpectedInt
	ExpectIncrByFloat(key string, value float64) *ExpectedFloat
	ExpectMGet(keys ...string) *ExpectedSlice
	ExpectMSet(values ...interface{}) *ExpectedStatus
	ExpectMSetNX(values ...interface{}) *ExpectedBool
	ExpectSet(key string, value interface{}, expiration time.Duration) *ExpectedStatus
	ExpectSetArgs(key string, value interface{}, a redis.SetArgs) *ExpectedStatus
	ExpectSetEx(key string, value interface{}, expiration time.Duration) *ExpectedStatus
	ExpectSetNX(key string, value interface{}, expiration time.Duration) *ExpectedBool
	ExpectSetXX(key string, value interface{}, expiration time.Duration) *ExpectedBool
	ExpectSetRange(key string, offset int64, value string) *ExpectedInt
	ExpectStrLen(key string) *ExpectedInt
	ExpectCopy(sourceKey string, destKey string, db int, replace bool) *ExpectedInt

	ExpectGetBit(key string, offset int64) *ExpectedInt
	ExpectSetBit(key string, offset int64, value int) *ExpectedInt
	ExpectBitCount(key string, bitCount *redis.BitCount) *ExpectedInt
	ExpectBitOpAnd(destKey string, keys ...string) *ExpectedInt
	ExpectBitOpOr(destKey string, keys ...string) *ExpectedInt
	ExpectBitOpXor(destKey string, keys ...string) *ExpectedInt
	ExpectBitOpNot(destKey string, key string) *ExpectedInt
	ExpectBitPos(key string, bit int64, pos ...int64) *ExpectedInt
	ExpectBitPosSpan(key string, bit int8, start, end int64, span string) *ExpectedInt
	ExpectBitField(key string, args ...interface{}) *ExpectedIntSlice

	ExpectScan(cursor uint64, match string, count int64) *ExpectedScan
	ExpectScanType(cursor uint64, match string, count int64, keyType string) *ExpectedScan
	ExpectSScan(key string, cursor uint64, match string, count int64) *ExpectedScan
	ExpectHScan(key string, cursor uint64, match string, count int64) *ExpectedScan
	ExpectZScan(key string, cursor uint64, match string, count int64) *ExpectedScan

	ExpectHDel(key string, fields ...string) *ExpectedInt
	ExpectHExists(key, field string) *ExpectedBool
	ExpectHGet(key, field string) *ExpectedString
	ExpectHGetAll(key string) *ExpectedMapStringString
	ExpectHIncrBy(key, field string, incr int64) *ExpectedInt
	ExpectHIncrByFloat(key, field string, incr float64) *ExpectedFloat
	ExpectHKeys(key string) *ExpectedStringSlice
	ExpectHLen(key string) *ExpectedInt
	ExpectHMGet(key string, fields ...string) *ExpectedSlice
	ExpectHSet(key string, values ...interface{}) *ExpectedInt
	ExpectHMSet(key string, values ...interface{}) *ExpectedBool
	ExpectHSetNX(key, field string, value interface{}) *ExpectedBool
	ExpectHVals(key string) *ExpectedStringSlice
	ExpectHRandField(key string, count int) *ExpectedStringSlice
	ExpectHRandFieldWithValues(key string, count int) *ExpectedKeyValueSlice

	ExpectBLPop(timeout time.Duration, keys ...string) *ExpectedStringSlice
	ExpectBLMPop(timeout time.Duration, direction string, count int64, keys ...string) *ExpectedKeyValues
	ExpectBRPop(timeout time.Duration, keys ...string) *ExpectedStringSlice
	ExpectBRPopLPush(source, destination string, timeout time.Duration) *ExpectedString
	ExpectLCS(q *redis.LCSQuery) *ExpectedLCS
	ExpectLIndex(key string, index int64) *ExpectedString
	ExpectLInsert(key, op string, pivot, value interface{}) *ExpectedInt
	ExpectLInsertBefore(key string, pivot, value interface{}) *ExpectedInt
	ExpectLInsertAfter(key string, pivot, value interface{}) *ExpectedInt
	ExpectLLen(key string) *ExpectedInt
	ExpectLPop(key string) *ExpectedString
	ExpectLPopCount(key string, count int) *ExpectedStringSlice
	ExpectLMPop(direction string, count int64, keys ...string) *ExpectedKeyValues
	ExpectLPos(key string, value string, args redis.LPosArgs) *ExpectedInt
	ExpectLPosCount(key string, value string, count int64, args redis.LPosArgs) *ExpectedIntSlice
	ExpectLPush(key string, values ...interface{}) *ExpectedInt
	ExpectLPushX(key string, values ...interface{}) *ExpectedInt
	ExpectLRange(key string, start, stop int64) *ExpectedStringSlice
	ExpectLRem(key string, count int64, value interface{}) *ExpectedInt
	ExpectLSet(key string, index int64, value interface{}) *ExpectedStatus
	ExpectLTrim(key string, start, stop int64) *ExpectedStatus
	ExpectRPop(key string) *ExpectedString
	ExpectRPopCount(key string, count int) *ExpectedStringSlice
	ExpectRPopLPush(source, destination string) *ExpectedString
	ExpectRPush(key string, values ...interface{}) *ExpectedInt
	ExpectRPushX(key string, values ...interface{}) *ExpectedInt
	ExpectLMove(source, destination, srcpos, destpos string) *ExpectedString
	ExpectBLMove(source, destination, srcpos, destpos string, timeout time.Duration) *ExpectedString

	ExpectSAdd(key string, members ...interface{}) *ExpectedInt
	ExpectSCard(key string) *ExpectedInt
	ExpectSDiff(keys ...string) *ExpectedStringSlice
	ExpectSDiffStore(destination string, keys ...string) *ExpectedInt
	ExpectSInter(keys ...string) *ExpectedStringSlice
	ExpectSInterCard(limit int64, keys ...string) *ExpectedInt
	ExpectSInterStore(destination string, keys ...string) *ExpectedInt
	ExpectSIsMember(key string, member interface{}) *ExpectedBool
	ExpectSMIsMember(key string, members ...interface{}) *ExpectedBoolSlice
	ExpectSMembers(key string) *ExpectedStringSlice
	ExpectSMembersMap(key string) *ExpectedStringStructMap
	ExpectSMove(source, destination string, member interface{}) *ExpectedBool
	ExpectSPop(key string) *ExpectedString
	ExpectSPopN(key string, count int64) *ExpectedStringSlice
	ExpectSRandMember(key string) *ExpectedString
	ExpectSRandMemberN(key string, count int64) *ExpectedStringSlice
	ExpectSRem(key string, members ...interface{}) *ExpectedInt
	ExpectSUnion(keys ...string) *ExpectedStringSlice
	ExpectSUnionStore(destination string, keys ...string) *ExpectedInt

	ExpectXAdd(a *redis.XAddArgs) *ExpectedString
	ExpectXDel(stream string, ids ...string) *ExpectedInt
	ExpectXLen(stream string) *ExpectedInt
	ExpectXRange(stream, start, stop string) *ExpectedXMessageSlice
	ExpectXRangeN(stream, start, stop string, count int64) *ExpectedXMessageSlice
	ExpectXRevRange(stream string, start, stop string) *ExpectedXMessageSlice
	ExpectXRevRangeN(stream string, start, stop string, count int64) *ExpectedXMessageSlice
	ExpectXRead(a *redis.XReadArgs) *ExpectedXStreamSlice
	ExpectXReadStreams(streams ...string) *ExpectedXStreamSlice
	ExpectXGroupCreate(stream, group, start string) *ExpectedStatus
	ExpectXGroupCreateMkStream(stream, group, start string) *ExpectedStatus
	ExpectXGroupSetID(stream, group, start string) *ExpectedStatus
	ExpectXGroupDestroy(stream, group string) *ExpectedInt
	ExpectXGroupCreateConsumer(stream, group, consumer string) *ExpectedInt
	ExpectXGroupDelConsumer(stream, group, consumer string) *ExpectedInt
	ExpectXReadGroup(a *redis.XReadGroupArgs) *ExpectedXStreamSlice
	ExpectXAck(stream, group string, ids ...string) *ExpectedInt
	ExpectXPending(stream, group string) *ExpectedXPending
	ExpectXPendingExt(a *redis.XPendingExtArgs) *ExpectedXPendingExt
	ExpectXClaim(a *redis.XClaimArgs) *ExpectedXMessageSlice
	ExpectXClaimJustID(a *redis.XClaimArgs) *ExpectedStringSlice
	ExpectXAutoClaim(a *redis.XAutoClaimArgs) *ExpectedXAutoClaim
	ExpectXAutoClaimJustID(a *redis.XAutoClaimArgs) *ExpectedXAutoClaimJustID
	ExpectXTrimMaxLen(key string, maxLen int64) *ExpectedInt
	ExpectXTrimMaxLenApprox(key string, maxLen, limit int64) *ExpectedInt
	ExpectXTrimMinID(key string, minID string) *ExpectedInt
	ExpectXTrimMinIDApprox(key string, minID string, limit int64) *ExpectedInt
	ExpectXInfoGroups(key string) *ExpectedXInfoGroups
	ExpectXInfoStream(key string) *ExpectedXInfoStream
	ExpectXInfoStreamFull(key string, count int) *ExpectedXInfoStreamFull
	ExpectXInfoConsumers(key string, group string) *ExpectedXInfoConsumers

	ExpectBZPopMax(timeout time.Duration, keys ...string) *ExpectedZWithKey
	ExpectBZPopMin(timeout time.Duration, keys ...string) *ExpectedZWithKey
	ExpectBZMPop(timeout time.Duration, order string, count int64, keys ...string) *ExpectedZSliceWithKey

	ExpectZAdd(key string, members ...redis.Z) *ExpectedInt
	ExpectZAddLT(key string, members ...redis.Z) *ExpectedInt
	ExpectZAddGT(key string, members ...redis.Z) *ExpectedInt
	ExpectZAddNX(key string, members ...redis.Z) *ExpectedInt
	ExpectZAddXX(key string, members ...redis.Z) *ExpectedInt
	ExpectZAddArgs(key string, args redis.ZAddArgs) *ExpectedInt
	ExpectZAddArgsIncr(key string, args redis.ZAddArgs) *ExpectedFloat
	ExpectZCard(key string) *ExpectedInt
	ExpectZCount(key, min, max string) *ExpectedInt
	ExpectZLexCount(key, min, max string) *ExpectedInt
	ExpectZIncrBy(key string, increment float64, member string) *ExpectedFloat
	ExpectZInter(store *redis.ZStore) *ExpectedStringSlice
	ExpectZInterWithScores(store *redis.ZStore) *ExpectedZSlice
	ExpectZInterCard(limit int64, keys ...string) *ExpectedInt
	ExpectZInterStore(destination string, store *redis.ZStore) *ExpectedInt
	ExpectZMPop(order string, count int64, keys ...string) *ExpectedZSliceWithKey
	ExpectZMScore(key string, members ...string) *ExpectedFloatSlice
	ExpectZPopMax(key string, count ...int64) *ExpectedZSlice
	ExpectZPopMin(key string, count ...int64) *ExpectedZSlice
	ExpectZRange(key string, start, stop int64) *ExpectedStringSlice
	ExpectZRangeWithScores(key string, start, stop int64) *ExpectedZSlice
	ExpectZRangeByScore(key string, opt *redis.ZRangeBy) *ExpectedStringSlice
	ExpectZRangeByLex(key string, opt *redis.ZRangeBy) *ExpectedStringSlice
	ExpectZRangeByScoreWithScores(key string, opt *redis.ZRangeBy) *ExpectedZSlice
	ExpectZRangeArgs(z redis.ZRangeArgs) *ExpectedStringSlice
	ExpectZRangeArgsWithScores(z redis.ZRangeArgs) *ExpectedZSlice
	ExpectZRangeStore(dst string, z redis.ZRangeArgs) *ExpectedInt
	ExpectZRank(key, member string) *ExpectedInt
	ExpectZRem(key string, members ...interface{}) *ExpectedInt
	ExpectZRemRangeByRank(key string, start, stop int64) *ExpectedInt
	ExpectZRemRangeByScore(key, min, max string) *ExpectedInt
	ExpectZRemRangeByLex(key, min, max string) *ExpectedInt
	ExpectZRevRange(key string, start, stop int64) *ExpectedStringSlice
	ExpectZRevRangeWithScores(key string, start, stop int64) *ExpectedZSlice
	ExpectZRevRangeByScore(key string, opt *redis.ZRangeBy) *ExpectedStringSlice
	ExpectZRevRangeByLex(key string, opt *redis.ZRangeBy) *ExpectedStringSlice
	ExpectZRevRangeByScoreWithScores(key string, opt *redis.ZRangeBy) *ExpectedZSlice
	ExpectZRevRank(key, member string) *ExpectedInt
	ExpectZScore(key, member string) *ExpectedFloat
	ExpectZUnionStore(dest string, store *redis.ZStore) *ExpectedInt
	ExpectZRandMember(key string, count int) *ExpectedStringSlice
	ExpectZRandMemberWithScores(key string, count int) *ExpectedZSlice
	ExpectZUnion(store redis.ZStore) *ExpectedStringSlice
	ExpectZUnionWithScores(store redis.ZStore) *ExpectedZSlice
	ExpectZDiff(keys ...string) *ExpectedStringSlice
	ExpectZDiffWithScores(keys ...string) *ExpectedZSlice
	ExpectZDiffStore(destination string, keys ...string) *ExpectedInt

	ExpectPFAdd(key string, els ...interface{}) *ExpectedInt
	ExpectPFCount(keys ...string) *ExpectedInt
	ExpectPFMerge(dest string, keys ...string) *ExpectedStatus

	ExpectBgRewriteAOF() *ExpectedStatus
	ExpectBgSave() *ExpectedStatus
	ExpectClientKill(ipPort string) *ExpectedStatus
	ExpectClientKillByFilter(keys ...string) *ExpectedInt
	ExpectClientList() *ExpectedString
	ExpectClientPause(dur time.Duration) *ExpectedBool
	ExpectClientUnpause() *ExpectedBool
	ExpectClientID() *ExpectedInt
	ExpectClientUnblock(id int64) *ExpectedInt
	ExpectClientUnblockWithError(id int64) *ExpectedInt
	ExpectConfigGet(parameter string) *ExpectedMapStringString
	ExpectConfigResetStat() *ExpectedStatus
	ExpectConfigSet(parameter, value string) *ExpectedStatus
	ExpectConfigRewrite() *ExpectedStatus
	ExpectDBSize() *ExpectedInt
	ExpectFlushAll() *ExpectedStatus
	ExpectFlushAllAsync() *ExpectedStatus
	ExpectFlushDB() *ExpectedStatus
	ExpectFlushDBAsync() *ExpectedStatus
	ExpectInfo(section ...string) *ExpectedString
	ExpectLastSave() *ExpectedInt
	ExpectSave() *ExpectedStatus
	ExpectShutdown() *ExpectedStatus
	ExpectShutdownSave() *ExpectedStatus
	ExpectShutdownNoSave() *ExpectedStatus
	ExpectSlaveOf(host, port string) *ExpectedStatus
	ExpectSlowLogGet(num int64) *ExpectedSlowLog
	ExpectTime() *ExpectedTime
	ExpectDebugObject(key string) *ExpectedString
	ExpectReadOnly() *ExpectedStatus
	ExpectReadWrite() *ExpectedStatus
	ExpectMemoryUsage(key string, samples ...int) *ExpectedInt

	ExpectEval(script string, keys []string, args ...interface{}) *ExpectedCmd
	ExpectEvalSha(sha1 string, keys []string, args ...interface{}) *ExpectedCmd
	ExpectEvalRO(script string, keys []string, args ...interface{}) *ExpectedCmd
	ExpectEvalShaRO(sha1 string, keys []string, args ...interface{}) *ExpectedCmd
	ExpectScriptExists(hashes ...string) *ExpectedBoolSlice
	ExpectScriptFlush() *ExpectedStatus
	ExpectScriptKill() *ExpectedStatus
	ExpectScriptLoad(script string) *ExpectedString

	ExpectPublish(channel string, message interface{}) *ExpectedInt
	ExpectSPublish(channel string, message interface{}) *ExpectedInt
	ExpectPubSubChannels(pattern string) *ExpectedStringSlice
	ExpectPubSubNumSub(channels ...string) *ExpectedMapStringInt
	ExpectPubSubNumPat() *ExpectedInt
	ExpectPubSubShardChannels(pattern string) *ExpectedStringSlice
	ExpectPubSubShardNumSub(channels ...string) *ExpectedMapStringInt

	ExpectClusterSlots() *ExpectedClusterSlots
	ExpectClusterShards() *ExpectedClusterShards
	ExpectClusterLinks() *ExpectedClusterLinks
	ExpectClusterNodes() *ExpectedString
	ExpectClusterMeet(host, port string) *ExpectedStatus
	ExpectClusterForget(nodeID string) *ExpectedStatus
	ExpectClusterReplicate(nodeID string) *ExpectedStatus
	ExpectClusterResetSoft() *ExpectedStatus
	ExpectClusterResetHard() *ExpectedStatus
	ExpectClusterInfo() *ExpectedString
	ExpectClusterKeySlot(key string) *ExpectedInt
	ExpectClusterGetKeysInSlot(slot int, count int) *ExpectedStringSlice
	ExpectClusterCountFailureReports(nodeID string) *ExpectedInt
	ExpectClusterCountKeysInSlot(slot int) *ExpectedInt
	ExpectClusterDelSlots(slots ...int) *ExpectedStatus
	ExpectClusterDelSlotsRange(min, max int) *ExpectedStatus
	ExpectClusterSaveConfig() *ExpectedStatus
	ExpectClusterSlaves(nodeID string) *ExpectedStringSlice
	ExpectClusterFailover() *ExpectedStatus
	ExpectClusterAddSlots(slots ...int) *ExpectedStatus
	ExpectClusterAddSlotsRange(min, max int) *ExpectedStatus

	ExpectGeoAdd(key string, geoLocation ...*redis.GeoLocation) *ExpectedInt
	ExpectGeoPos(key string, members ...string) *ExpectedGeoPos
	ExpectGeoRadius(key string, longitude, latitude float64, query *redis.GeoRadiusQuery) *ExpectedGeoLocation
	ExpectGeoRadiusStore(key string, longitude, latitude float64, query *redis.GeoRadiusQuery) *ExpectedInt
	ExpectGeoRadiusByMember(key, member string, query *redis.GeoRadiusQuery) *ExpectedGeoLocation
	ExpectGeoRadiusByMemberStore(key, member string, query *redis.GeoRadiusQuery) *ExpectedInt
	ExpectGeoSearch(key string, q *redis.GeoSearchQuery) *ExpectedStringSlice
	ExpectGeoSearchLocation(key string, q *redis.GeoSearchLocationQuery) *ExpectedGeoSearchLocation
	ExpectGeoSearchStore(key, store string, q *redis.GeoSearchStoreQuery) *ExpectedInt
	ExpectGeoDist(key string, member1, member2, unit string) *ExpectedFloat
	ExpectGeoHash(key string, members ...string) *ExpectedStringSlice

	ExpectFunctionLoad(code string) *ExpectedString
	ExpectFunctionLoadReplace(code string) *ExpectedString
	ExpectFunctionDelete(libName string) *ExpectedString
	ExpectFunctionFlush() *ExpectedString
	ExpectFunctionFlushAsync() *ExpectedString
	ExpectFunctionList(q redis.FunctionListQuery) *ExpectedFunctionList
	ExpectFunctionKill() *ExpectedString
	ExpectFunctionDump() *ExpectedString
	ExpectFunctionRestore(libDump string) *ExpectedString
	ExpectFCall(function string, keys []string, args ...interface{}) *ExpectedCmd
	ExpectFCallRo(function string, keys []string, args ...interface{}) *ExpectedCmd

	ExpectACLDryRun(username string, command ...interface{}) *ExpectedString
}

type pipelineMock interface {
	ExpectTxPipeline()
	ExpectTxPipelineExec() *ExpectedSlice
}

type watchMock interface {
	ExpectWatch(keys ...string) *ExpectedError
}

type ClientMock interface {
	baseMock
	pipelineMock
	watchMock
}

type ClusterClientMock interface {
	baseMock
}

func inflow(cmd redis.Cmder, key string, val interface{}) {
	v := reflect.ValueOf(cmd).Elem().FieldByName(key)
	if !v.IsValid() {
		panic(fmt.Sprintf("cmd did not find key '%s'", key))
	}
	v = reflect.NewAt(v.Type(), unsafe.Pointer(v.UnsafeAddr())).Elem()

	setVal := reflect.ValueOf(val)
	if v.Kind() != reflect.Interface && setVal.Kind() != v.Kind() {
		panic(fmt.Sprintf("expected kind %v, got kind: %v", v.Kind(), setVal.Kind()))
	}
	v.Set(setVal)
}

type expectation interface {
	regexp() bool
	setRegexpMatch()
	custom() CustomMatch
	setCustomMatch(fn CustomMatch)
	usable() bool
	trigger()

	name() string
	args() []interface{}

	error() error
	SetErr(err error)

	RedisNil()
	isRedisNil() bool

	inflow(c redis.Cmder)

	isSetVal() bool

	lock()
	unlock()
}

type CustomMatch func(expected, actual []interface{}) error

type expectedBase struct {
	cmd         redis.Cmder
	err         error
	redisNil    bool
	triggered   bool
	setVal      bool
	regexpMatch bool
	customMatch CustomMatch

	rw sync.RWMutex
}

func (base *expectedBase) lock() {
	base.rw.Lock()
}

func (base *expectedBase) unlock() {
	base.rw.Unlock()
}

func (base *expectedBase) regexp() bool {
	return base.regexpMatch
}

func (base *expectedBase) setRegexpMatch() {
	base.regexpMatch = true
}

func (base *expectedBase) custom() CustomMatch {
	return base.customMatch
}

func (base *expectedBase) setCustomMatch(fn CustomMatch) {
	base.customMatch = fn
}

func (base *expectedBase) usable() bool {
	return !base.triggered
}

func (base *expectedBase) trigger() {
	base.triggered = true
}

func (base *expectedBase) name() string {
	return base.cmd.Name()
}

func (base *expectedBase) args() []interface{} {
	return base.cmd.Args()
}

func (base *expectedBase) SetErr(err error) {
	base.err = err
}

func (base *expectedBase) error() error {
	return base.err
}

func (base *expectedBase) RedisNil() {
	base.redisNil = true
}

func (base *expectedBase) isRedisNil() bool {
	return base.redisNil
}

func (base *expectedBase) isSetVal() bool {
	return base.setVal
}

//---------------------------------

type ExpectedCommandsInfo struct {
	expectedBase

	val map[string]*redis.CommandInfo
}

func (cmd *ExpectedCommandsInfo) SetVal(val []*redis.CommandInfo) {
	cmd.setVal = true
	cmd.val = make(map[string]*redis.CommandInfo)
	for _, v := range val {
		cmd.val[v.Name] = v
	}
}

func (cmd *ExpectedCommandsInfo) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedString struct {
	expectedBase

	val string
}

func (cmd *ExpectedString) SetVal(val string) {
	cmd.setVal = true
	cmd.val = val
}

func (cmd *ExpectedString) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedStatus struct {
	expectedBase

	val string
}

func (cmd *ExpectedStatus) SetVal(val string) {
	cmd.setVal = true
	cmd.val = val
}

func (cmd *ExpectedStatus) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedInt struct {
	expectedBase

	val int64
}

func (cmd *ExpectedInt) SetVal(val int64) {
	cmd.setVal = true
	cmd.val = val
}

func (cmd *ExpectedInt) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedBool struct {
	expectedBase

	val bool
}

func (cmd *ExpectedBool) SetVal(val bool) {
	cmd.setVal = true
	cmd.val = val
}

func (cmd *ExpectedBool) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedStringSlice struct {
	expectedBase

	val []string
}

func (cmd *ExpectedStringSlice) SetVal(val []string) {
	cmd.setVal = true
	cmd.val = make([]string, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedStringSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedKeyValueSlice struct {
	expectedBase

	val []redis.KeyValue
}

func (cmd *ExpectedKeyValueSlice) SetVal(val []redis.KeyValue) {
	cmd.setVal = true
	cmd.val = make([]redis.KeyValue, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedKeyValueSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedDuration struct {
	expectedBase

	val time.Duration
	// precision time.Duration
}

func (cmd *ExpectedDuration) SetVal(val time.Duration) {
	cmd.setVal = true
	cmd.val = val
}

func (cmd *ExpectedDuration) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedSlice struct {
	expectedBase

	val []interface{}
}

func (cmd *ExpectedSlice) SetVal(val []interface{}) {
	cmd.setVal = true
	cmd.val = make([]interface{}, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedFloat struct {
	expectedBase

	val float64
}

func (cmd *ExpectedFloat) SetVal(val float64) {
	cmd.setVal = true
	cmd.val = val
}

func (cmd *ExpectedFloat) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedFloatSlice struct {
	expectedBase

	val []float64
}

func (cmd *ExpectedFloatSlice) SetVal(val []float64) {
	cmd.setVal = true
	cmd.val = make([]float64, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedFloatSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedIntSlice struct {
	expectedBase

	val []int64
}

func (cmd *ExpectedIntSlice) SetVal(val []int64) {
	cmd.setVal = true
	cmd.val = make([]int64, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedIntSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedScan struct {
	expectedBase

	page   []string
	cursor uint64
}

func (cmd *ExpectedScan) SetVal(page []string, cursor uint64) {
	cmd.setVal = true
	cmd.page = make([]string, len(page))
	copy(cmd.page, page)
	cmd.cursor = cursor
}

func (cmd *ExpectedScan) inflow(c redis.Cmder) {
	inflow(c, "page", cmd.page)
	inflow(c, "cursor", cmd.cursor)
}

// ------------------------------------------------------------

type ExpectedMapStringString struct {
	expectedBase

	val map[string]string
}

func (cmd *ExpectedMapStringString) SetVal(val map[string]string) {
	cmd.setVal = true
	cmd.val = make(map[string]string)
	for k, v := range val {
		cmd.val[k] = v
	}
}

func (cmd *ExpectedMapStringString) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedStringStructMap struct {
	expectedBase

	val map[string]struct{}
}

func (cmd *ExpectedStringStructMap) SetVal(val []string) {
	cmd.setVal = true
	cmd.val = make(map[string]struct{})
	for _, v := range val {
		cmd.val[v] = struct{}{}
	}
}

func (cmd *ExpectedStringStructMap) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedXMessageSlice struct {
	expectedBase

	val []redis.XMessage
}

func (cmd *ExpectedXMessageSlice) SetVal(val []redis.XMessage) {
	cmd.setVal = true
	cmd.val = make([]redis.XMessage, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedXMessageSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedXStreamSlice struct {
	expectedBase

	val []redis.XStream
}

func (cmd *ExpectedXStreamSlice) SetVal(val []redis.XStream) {
	cmd.setVal = true
	cmd.val = make([]redis.XStream, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedXStreamSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedXPending struct {
	expectedBase

	val *redis.XPending
}

func (cmd *ExpectedXPending) SetVal(val *redis.XPending) {
	cmd.setVal = true
	v := *val
	cmd.val = &v
}

func (cmd *ExpectedXPending) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedXPendingExt struct {
	expectedBase

	val []redis.XPendingExt
}

func (cmd *ExpectedXPendingExt) SetVal(val []redis.XPendingExt) {
	cmd.setVal = true
	cmd.val = make([]redis.XPendingExt, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedXPendingExt) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ----------------------------------------------------------------------

type ExpectedXAutoClaim struct {
	expectedBase

	start string
	val   []redis.XMessage
}

func (cmd *ExpectedXAutoClaim) SetVal(val []redis.XMessage, start string) {
	cmd.setVal = true
	cmd.start = start
	cmd.val = make([]redis.XMessage, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedXAutoClaim) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
	inflow(c, "start", cmd.start)
}

// ------------------------------------------------------------

type ExpectedXAutoClaimJustID struct {
	expectedBase

	start string
	val   []string
}

func (cmd *ExpectedXAutoClaimJustID) SetVal(val []string, start string) {
	cmd.setVal = true
	cmd.start = start
	cmd.val = make([]string, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedXAutoClaimJustID) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
	inflow(c, "start", cmd.start)
}

// ------------------------------------------------------------

type ExpectedXInfoGroups struct {
	expectedBase

	val []redis.XInfoGroup
}

func (cmd *ExpectedXInfoGroups) SetVal(val []redis.XInfoGroup) {
	cmd.setVal = true
	cmd.val = make([]redis.XInfoGroup, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedXInfoGroups) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedXInfoStream struct {
	expectedBase

	val *redis.XInfoStream
}

func (cmd *ExpectedXInfoStream) SetVal(val *redis.XInfoStream) {
	cmd.setVal = true
	v := *val
	cmd.val = &v
}

func (cmd *ExpectedXInfoStream) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedXInfoConsumers struct {
	expectedBase

	val []redis.XInfoConsumer
}

func (cmd *ExpectedXInfoConsumers) SetVal(val []redis.XInfoConsumer) {
	cmd.setVal = true
	cmd.val = make([]redis.XInfoConsumer, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedXInfoConsumers) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedXInfoStreamFull struct {
	expectedBase

	val *redis.XInfoStreamFull
}

func (cmd *ExpectedXInfoStreamFull) SetVal(val *redis.XInfoStreamFull) {
	cmd.setVal = true
	v := *val
	cmd.val = &v
}

func (cmd *ExpectedXInfoStreamFull) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedZWithKey struct {
	expectedBase

	val *redis.ZWithKey
}

func (cmd *ExpectedZWithKey) SetVal(val *redis.ZWithKey) {
	cmd.setVal = true
	v := *val
	cmd.val = &v
}

func (cmd *ExpectedZWithKey) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedZSlice struct {
	expectedBase

	val []redis.Z
}

func (cmd *ExpectedZSlice) SetVal(val []redis.Z) {
	cmd.setVal = true
	cmd.val = make([]redis.Z, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedZSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedTime struct {
	expectedBase

	val time.Time
}

func (cmd *ExpectedTime) SetVal(val time.Time) {
	cmd.setVal = true
	cmd.val = val
}

func (cmd *ExpectedTime) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedCmd struct {
	expectedBase

	val interface{}
}

func (cmd *ExpectedCmd) SetVal(val interface{}) {
	cmd.setVal = true
	cmd.val = val
}

func (cmd *ExpectedCmd) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedBoolSlice struct {
	expectedBase

	val []bool
}

func (cmd *ExpectedBoolSlice) SetVal(val []bool) {
	cmd.setVal = true
	cmd.val = make([]bool, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedBoolSlice) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedClusterSlots struct {
	expectedBase

	val []redis.ClusterSlot
}

func (cmd *ExpectedClusterSlots) SetVal(val []redis.ClusterSlot) {
	cmd.setVal = true
	cmd.val = make([]redis.ClusterSlot, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedClusterSlots) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedClusterLinks struct {
	expectedBase

	val []redis.ClusterLink
}

func (cmd *ExpectedClusterLinks) SetVal(val []redis.ClusterLink) {
	cmd.setVal = true
	cmd.val = make([]redis.ClusterLink, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedClusterLinks) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedMapStringInt struct {
	expectedBase

	val map[string]int64
}

func (cmd *ExpectedMapStringInt) SetVal(val map[string]int64) {
	cmd.setVal = true
	cmd.val = make(map[string]int64)
	for k, v := range val {
		cmd.val[k] = v
	}
}

func (cmd *ExpectedMapStringInt) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedGeoPos struct {
	expectedBase

	val []*redis.GeoPos
}

func (cmd *ExpectedGeoPos) SetVal(val []*redis.GeoPos) {
	cmd.setVal = true
	cmd.val = make([]*redis.GeoPos, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedGeoPos) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedGeoLocation struct {
	expectedBase

	locations []redis.GeoLocation
}

func (cmd *ExpectedGeoLocation) SetVal(val []redis.GeoLocation) {
	cmd.setVal = true
	cmd.locations = make([]redis.GeoLocation, len(val))
	copy(cmd.locations, val)
}

func (cmd *ExpectedGeoLocation) inflow(c redis.Cmder) {
	inflow(c, "locations", cmd.locations)
}

// ------------------------------------------------------------

type ExpectedGeoSearchLocation struct {
	expectedBase

	val []redis.GeoLocation
}

func (cmd *ExpectedGeoSearchLocation) SetVal(val []redis.GeoLocation) {
	cmd.setVal = true
	cmd.val = make([]redis.GeoLocation, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedGeoSearchLocation) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedKeyValues struct {
	expectedBase

	key string
	val []string
}

func (cmd *ExpectedKeyValues) SetVal(key string, val []string) {
	cmd.setVal = true
	cmd.key = key
	cmd.val = make([]string, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedKeyValues) inflow(c redis.Cmder) {
	inflow(c, "key", cmd.key)
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedZSliceWithKey struct {
	expectedBase

	key string
	val []redis.Z
}

func (cmd *ExpectedZSliceWithKey) SetVal(key string, val []redis.Z) {
	cmd.setVal = true
	cmd.key = key
	cmd.val = make([]redis.Z, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedZSliceWithKey) inflow(c redis.Cmder) {
	inflow(c, "key", cmd.key)
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedSlowLog struct {
	expectedBase

	val []redis.SlowLog
}

func (cmd *ExpectedSlowLog) SetVal(val []redis.SlowLog) {
	cmd.setVal = true
	cmd.val = make([]redis.SlowLog, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedSlowLog) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedFunctionList struct {
	expectedBase

	val []redis.Library
}

func (cmd *ExpectedFunctionList) SetVal(val []redis.Library) {
	cmd.setVal = true
	cmd.val = make([]redis.Library, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedFunctionList) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedLCS struct {
	expectedBase

	val *redis.LCSMatch
}

func (cmd *ExpectedLCS) SetVal(val *redis.LCSMatch) {
	cmd.setVal = true
	v := *val
	cmd.val = &v
}

func (cmd *ExpectedLCS) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedKeyFlags struct {
	expectedBase

	val []redis.KeyFlags
}

func (cmd *ExpectedKeyFlags) SetVal(val []redis.KeyFlags) {
	cmd.setVal = true
	cmd.val = make([]redis.KeyFlags, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedKeyFlags) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedClusterShards struct {
	expectedBase

	val []redis.ClusterShard
}

func (cmd *ExpectedClusterShards) SetVal(val []redis.ClusterShard) {
	cmd.setVal = true
	cmd.val = make([]redis.ClusterShard, len(val))
	copy(cmd.val, val)
}

func (cmd *ExpectedClusterShards) inflow(c redis.Cmder) {
	inflow(c, "val", cmd.val)
}

// ------------------------------------------------------------

type ExpectedError struct {
	expectedBase
}

func (cmd *ExpectedError) inflow(c redis.Cmder) {}
