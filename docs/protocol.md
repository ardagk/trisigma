# Generic RPC via AMQP
routing key: name of the agent
message:
``` json
{
    "endpoint": "<endpoint">,
    "params": {}
}
```

# Generic PubSub
routing key: "<agentName>.<eventName#>"
message:
``` json
{
    "event_name": "<eventName>",
    "details": {},
}
```
