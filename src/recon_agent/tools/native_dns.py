"""One bounded native UDP exchange; no system resolver, retries or alias queries."""

from typing import Protocol

import dns.asyncquery
import dns.message


class DnsResolver(Protocol):
    async def exchange(
        self, query: dns.message.Message, nameserver: str, timeout_seconds: float
    ) -> dns.message.Message: ...


class NativeDnsResolver:
    async def exchange(
        self, query: dns.message.Message, nameserver: str, timeout_seconds: float
    ) -> dns.message.Message:
        # Numeric, scope-checked endpoint supplied only by trusted adapter code.
        # UDP's wire message is bounded at 65,535 bytes. No TCP fallback/retry.
        return await dns.asyncquery.udp(
            query,
            nameserver,
            timeout=timeout_seconds,
            port=53,
            ignore_unexpected=False,
            ignore_errors=False,
            raise_on_truncation=True,
        )
