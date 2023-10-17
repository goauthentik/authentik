from redis.asyncio import Sentinel as AsyncSentinel
from redis.sentinel import MasterNotFoundError, Sentinel


class CustomSentinel(Sentinel):
    def check_master_state(self, state, service_name):
        raise NotImplementedError

    def discover_master(self, service_name):
        """
        Asks sentinel servers for the Redis master's address corresponding
        to the service labeled ``service_name``.
        Returns a pair (address, port) or raises MasterNotFoundError if no
        master is found.
        """
        collected_errors = list()
        for sentinel_no, sentinel in enumerate(self.sentinels):
            try:
                master = sentinel.sentinel_get_master_addr_by_name(service_name)
            except (ConnectionError, TimeoutError) as exc:
                collected_errors.append(f"{sentinel} - {exc!r}")
                continue
            if master:
                # Put this sentinel at the top of the list
                self.sentinels[0], self.sentinels[sentinel_no] = (sentinel, self.sentinels[0])
                return master[0], master[1]

        error_info = ""
        if len(collected_errors) > 0:
            error_info = f" : {', '.join(collected_errors)}"
        raise MasterNotFoundError(f"No master found for {service_name!r}{error_info}")


class CustomAsyncSentinel(AsyncSentinel):
    def check_master_state(self, state: dict, service_name: str) -> bool:
        raise NotImplementedError

    async def discover_master(self, service_name: str):
        """
        Asks sentinel servers for the Redis master's address corresponding
        to the service labeled ``service_name``.

        Returns a pair (address, port) or raises MasterNotFoundError if no
        master is found.
        """
        collected_errors = list()
        for sentinel_no, sentinel in enumerate(self.sentinels):
            try:
                master = await sentinel.sentinel_get_master_addr_by_name(service_name)
            except (ConnectionError, TimeoutError) as exc:
                collected_errors.append(f"{sentinel} - {exc!r}")
                continue
            if master:
                # Put this sentinel at the top of the list
                self.sentinels[0], self.sentinels[sentinel_no] = (sentinel, self.sentinels[0])
                return master[0], master[1]

        error_info = ""
        if len(collected_errors) > 0:
            error_info = f" : {', '.join(collected_errors)}"
        raise MasterNotFoundError(f"No master found for {service_name!r}{error_info}")
