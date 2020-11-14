from lets.__module__ import Module, Container


class Socks(Module):
    """
    Proxy SOCKS4/SOCKS5 traffic over TOR.
    """
    images = [
        "dperson/torproxy:latest",      # Cross-platform, no versions
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-p", "--port", type=int, help="listen on port", default=9050)
        parser.add_argument("--interface", type=str, help="listen on interface", default="0.0.0.0")
        parser.add_argument("--country", type=str, help="emerge from country code")
        # Mitmproxy does not have upstream:socks5, cannot mitm

    def handle(self, input, port=9050, interface="0.0.0.0", country=None):

        # Construct command
        cmd = ""

        if country:
            self.log.info("Using country code: %s", country)
            cmd += " -l %s" % country

        # Launch tor
        self.log.info("Connecting to tor...")
        with Container.run("dperson/torproxy:latest",
            ports={"9050/tcp" : (interface, port)},
            command=cmd) as vpn:
           
            # Wait for successful connection
            for log in vpn.logs(stream=True, follow=True):
                self.log.logger.debug(log.strip().decode())
                if b"Bootstrapped 100% (done): Done" in log:
                    self.log.info("Connected to tor, listening on %s:%i", interface, port)
