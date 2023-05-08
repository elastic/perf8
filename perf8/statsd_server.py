import asyncio
import statsd
from collections import defaultdict
import functools


HOST, PORT = "localhost", 514


async def write_messages():
    c = statsd.StatsClient("localhost", 514)
    c.incr("foo")
    c.timing("stats.timed", 320)


class StatsdData:
    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = defaultdict(int)
        self.sets = defaultdict(set)

    def __str__(self):
        return (
            f"counters: {self.counters}\n"
            f"timers: {self.timers}\n"
            f"gauges: {self.gauges}\n"
            f"sets: {self.sets}\n"
        )


class StatsdProtocol(asyncio.DatagramProtocol):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        data = data.split(b"|")
        data_type = data[1]
        ns, metric = data[0].split(b":")

        if data_type == b"c":
            self._data.counters[ns] += int(metric)

        elif data_type == b"g":
            if metric.startswith("+", "-"):
                self._data.gauges[ns] += int(metric)
            else:
                self._data.gauges[ns] = int(metric)

        elif data_type == b"ms":
            self._data.timers[ns].append(float(metric))

        elif data_type == b"s":
            self._data.sets[ns].add(int(metric))

        print(self._data)


async def start(data, port):
    loop = asyncio.get_event_loop()
    return loop.create_datagram_endpoint(
        functools.partial(StatsdProtocol, data), local_addr=("0.0.0.0", port)
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    d = StatsdData()
    loop.run_until_complete(start(d, PORT))
    loop.run_until_complete(
        write_messages()
    )  # Start writing messages (or running tests)
    loop.run_forever()
