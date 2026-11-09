import "../ak-attribute-view";
import type { AttributeViewProps } from "./AttributeView.builder";

import type { Meta, StoryObj } from "@storybook/web-components-vite";

import { html } from "lit";

const meta = {
    title: "Elements / <ak-attribute-view>",
    component: "ak-attribute-view",
    tags: ["autodocs"],
    argTypes: {
        value: { control: "object" },
        mode: {
            control: { type: "select" },
            options: ["json", "yaml", "tree"],
        },
    },
} satisfies Meta;

export default meta;

type Story = StoryObj;

const Template: Story = {
    args: {
        value: {},
        mode: "json",
    },
    render: (args) => {
        return html` <ak-attribute-view
            mode=${args.mode}
            .value=${args.value}
        ></ak-attribute-view>`;
    },
};

export const Default: Story = {
    ...Template,
};

const story = (args: AttributeViewProps, value?: unknown): Story => ({
    ...Template,
    ...(value ? { value } : {}),
    args: {
        ...Template.args,
        ...args,
    },
});

const simpleMessage = {
    model: {
        pk: "02c2e030162d4140ab53a63fc84085c9",
        app: "authentik_core",
        name: "Admirable Commercial Razzmatazz RAC App (a2fdd5)",
        model_name: "application",
    },
};

export const Simple: Story = story({ value: simpleMessage });

const longMessage = {
    exception: [
        {
            frames: [
                {
                    name: "process_message",
                    lineno: 560,
                    locals: {
                        e: "LDAPServerPoolExhaustedError('no random active server available in server pool after maximum number of tries')",
                        res: "None",
                        self: "<WorkerThread(Thread-8, started daemon 6277099520)>",
                        actor: "Actor(<function ldap_sync at 0x1112e71c0>, queue_name='default', actor_name='authentik.sources.ldap.tasks.ldap_sync')",
                        throws: "None",
                        message:
                            '<MessageProxy Message(queue_name=\'default\', actor_name=\'authentik.sources.ldap.tasks.ldap_sync\', args=(UUID(\'d769c43a-efa6-4d6f-b160-e6a68fbf3dcc\'),), kwargs={}, options={\'model_create_defaults\': {\'tenant\': <Tenant: Tenant Default>}, \'task\': <Task: 9e3a1727-dfbe-4228-8f56-17d1784bc751>, \'retries\': 5, \'traceback\': \'Traceback (most recent call last):\\n  File "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/dramatiq/worker.py", line 560, in process_message\\n    res = actor(*message.args, **message.kwargs)\\n  File "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/dramatiq/actor.py", line 194, in __call__\\n    return self.fn(*args, **kwargs)\\n           ~~~~~~~^^^^^^^^^^^^^^^^^\\n  File "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/tasks.py", line 70, in ldap_sync\\n    ldap_sync_paginator(task, source, UserLDAPSynchronizer)\\n    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\\n  File "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/tasks.py", line 118, in ldap_sync_paginator\\n    sync_inst: BaseLDAPSynchronizer = sync(source, task)\\n                                      ~~~~^^^^^^^^^^^^^^\\n  File "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/sync/users.py", line 35, in __init__\\n    super().__init__(source, task)\\n    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^\\n  File "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/sync/base.py", line 35, in __init__\\n    self._connection = source.connection()\\n                       ~~~~~~~~~~~~~~~~~^^\\n  File "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/models.py", line 282, in connection\\n    conn.start_tls(read_server_info=False)\\n    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^\\n  File "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/core/connection.py", line 1313, in start_tls\\n    self.open()\\n    ~~~~~~~~~^^\\n  File "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/strategy/sync.py", line 57, in open\\n    BaseStrategy.open(self, reset_usage, read_server_info)\\n    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\\n  File "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/strategy/base.py", line 122, in open\\n    new_server = self.connection.server_pool.get_server(self.connection)  # get a server from the server_pool if available\\n  File "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/core/pooling.py", line 317, in get_server\\n    return self.pool_states[connection].get_server()\\n           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\\n  File "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/core/pooling.py", line 97, in get_server\\n    self.last_used_server = self.find_active_random_server()\\n                            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\\n  File "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/core/pooling.py", line 143, in find_active_random_server\\n    raise LDAPServerPoolExhaustedError(\\\'no random active server available in server pool after maximum number of tries\\\')\\nldap3.core.exceptions.LDAPServerPoolExhaustedError: no random active server available in server pool after maximum number of tries\\n\', \'requeue_timestamp\': 1783695391693}, message_id=\'9e3a1727-dfbe-4228-8f56-17d1784bc751\', message_timestamp=1783694945228)>',
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/dramatiq/worker.py",
                },
                {
                    name: "__call__",
                    lineno: 194,
                    locals: {
                        args: "(UUID('d769c43a-efa6-4d6f-b160-e6a68fbf3dcc'),)",
                        self: "Actor(<function ldap_sync at 0x1112e71c0>, queue_name='default', actor_name='authentik.sources.ldap.tasks.ldap_sync')",
                        delta: "15.008882874972187",
                        start: "361978.333430583",
                        kwargs: "{}",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/dramatiq/actor.py",
                },
                {
                    name: "ldap_sync",
                    lineno: 70,
                    locals: {
                        task: "<Task: 9e3a1727-dfbe-4228-8f56-17d1784bc751>",
                        source: "<LDAPSource: Some LDAP Server>",
                        source_pk: "UUID('d769c43a-efa6-4d6f-b160-e6a68fbf3dcc')",
                        lock_acquired: "True",
                    },
                    filename: "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/tasks.py",
                },
                {
                    name: "ldap_sync_paginator",
                    lineno: 118,
                    locals: {
                        sync: "<class 'authentik.sources.ldap.sync.users.UserLDAPSynchronizer'>",
                        task: "<Task: 9e3a1727-dfbe-4228-8f56-17d1784bc751>",
                        source: "<LDAPSource: Some LDAP Server>",
                    },
                    filename: "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/tasks.py",
                },
                {
                    name: "__init__",
                    lineno: 35,
                    locals: {
                        self: "<authentik.sources.ldap.sync.users.UserLDAPSynchronizer object at 0x113adb4d0>",
                        task: "<Task: 9e3a1727-dfbe-4228-8f56-17d1784bc751>",
                        source: "<LDAPSource: Some LDAP Server>",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/sync/users.py",
                },
                {
                    name: "__init__",
                    lineno: 35,
                    locals: {
                        self: "<authentik.sources.ldap.sync.users.UserLDAPSynchronizer object at 0x113adb4d0>",
                        task: "<Task: 9e3a1727-dfbe-4228-8f56-17d1784bc751>",
                        source: "<LDAPSource: Some LDAP Server>",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/sync/base.py",
                },
                {
                    name: "connection",
                    lineno: 282,
                    locals: {
                        conn: "Connection(server=ServerPool(servers=[Server(host='128.0.0.1', port=389, use_ssl=False, allowed_referral_hosts=[('*', True)], tls=Tls(validate=<VerifyMode.CERT_NONE: 0>), get_info='ALL', connect_timeout=15, mode='IP_V6_PREFERRED')], pool_strategy='RANDOM', active=5, exhaust=True), user='akadmin', password='test-runner', auto_bind='DEFAULT', version=3, authentication='SIMPLE', client_strategy='SYNC', auto_referrals=True, check_names=True, read_only=False, lazy=False, raise_exceptions=True, fast_decoder=True, auto_range=True, receive_timeout=15, return_empty_attributes=True, auto_encode=True, auto_escape=True, use_referral_cache=False)",
                        self: "<LDAPSource: Some LDAP Server>",
                        server: "None",
                        server_kwargs: "{}",
                        connection_kwargs: "{'user': 'akadmin', 'password': 'test-runner'}",
                    },
                    filename: "/Users/jeanlucpicard/projects/dev/authentik/sources/ldap/models.py",
                },
                {
                    name: "start_tls",
                    lineno: 1313,
                    locals: {
                        self: "Connection(server=ServerPool(servers=[Server(host='128.0.0.1', port=389, use_ssl=False, allowed_referral_hosts=[('*', True)], tls=Tls(validate=<VerifyMode.CERT_NONE: 0>), get_info='ALL', connect_timeout=15, mode='IP_V6_PREFERRED')], pool_strategy='RANDOM', active=5, exhaust=True), user='akadmin', password='test-runner', auto_bind='DEFAULT', version=3, authentication='SIMPLE', client_strategy='SYNC', auto_referrals=True, check_names=True, read_only=False, lazy=False, raise_exceptions=True, fast_decoder=True, auto_range=True, receive_timeout=15, return_empty_attributes=True, auto_encode=True, auto_escape=True, use_referral_cache=False)",
                        return_value: "False",
                        read_server_info: "False",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/core/connection.py",
                },
                {
                    name: "open",
                    lineno: 57,
                    locals: {
                        self: "<ldap3.strategy.sync.SyncStrategy object at 0x113ec3390>",
                        reset_usage: "True",
                        read_server_info: "True",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/strategy/sync.py",
                },
                {
                    name: "open",
                    lineno: 122,
                    locals: {
                        self: "<ldap3.strategy.sync.SyncStrategy object at 0x113ec3390>",
                        reset_usage: "True",
                        read_server_info: "True",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/strategy/base.py",
                },
                {
                    name: "get_server",
                    lineno: 317,
                    locals: {
                        self: "ServerPool(servers=[Server(host='128.0.0.1', port=389, use_ssl=False, allowed_referral_hosts=[('*', True)], tls=Tls(validate=<VerifyMode.CERT_NONE: 0>), get_info='ALL', connect_timeout=15, mode='IP_V6_PREFERRED')], pool_strategy='RANDOM', active=5, exhaust=True)",
                        connection:
                            "Connection(server=ServerPool(servers=[Server(host='128.0.0.1', port=389, use_ssl=False, allowed_referral_hosts=[('*', True)], tls=Tls(validate=<VerifyMode.CERT_NONE: 0>), get_info='ALL', connect_timeout=15, mode='IP_V6_PREFERRED')], pool_strategy='RANDOM', active=5, exhaust=True), user='akadmin', password='test-runner', auto_bind='DEFAULT', version=3, authentication='SIMPLE', client_strategy='SYNC', auto_referrals=True, check_names=True, read_only=False, lazy=False, raise_exceptions=True, fast_decoder=True, auto_range=True, receive_timeout=15, return_empty_attributes=True, auto_encode=True, auto_escape=True, use_referral_cache=False)",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/core/pooling.py",
                },
                {
                    name: "get_server",
                    lineno: 97,
                    locals: {
                        self: "<ldap3.core.pooling.ServerPoolState object at 0x113ad8ec0>",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/core/pooling.py",
                },
                {
                    name: "find_active_random_server",
                    lineno: 143,
                    locals: {
                        self: "<ldap3.core.pooling.ServerPoolState object at 0x113ad8ec0>",
                        counter: "0",
                        temp_list: "[]",
                        server_state: "<ldap3.core.pooling.ServerState object at 0x113dcd490>",
                    },
                    filename:
                        "/Users/jeanlucpicard/projects/dev/.venv/lib/python3.14/site-packages/ldap3/core/pooling.py",
                },
            ],
            exc_type: "LDAPServerPoolExhaustedError",
            is_cause: false,
            is_group: false,
            exc_notes: [],
            exc_value:
                "no random active server available in server pool after maximum number of tries",
            exceptions: [],
            syntax_error: null,
        },
    ],
};

export const Long: Story = story({ value: longMessage });
