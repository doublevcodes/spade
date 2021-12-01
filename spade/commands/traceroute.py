import random
import socket

PORT_RANGE = range(33434, 33535)


class Tracer:
    def __init__(self, host, hops):
        self.host: str = host
        self.hops: int = hops
        self.ttl: int = 1

        self.port = random.choice(PORT_RANGE)

    def run(self) -> None:
        ...
