from lets.__module__ import Module, Container


class Service(Module):
    """
    Proxy TCP traffic from TOR as a hidden service.
    """
    images = [
        "dperson/torproxy:latest",      # Cross-platform, no versions
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("lhost", type=str, help="local host")
        parser.add_argument("lport", type=int, help="local port")
        parser.add_argument("-p", "--port", type=int, help="remote port", default="80")

    def handle(self, input, lhost, lport, port=80):

        # Construct command
        cmd = "-s %s;%s:%s" % (port, lhost, lport)

        # Launch tor
        self.log.info("Connecting to tor...")
        with Container.run("dperson/torproxy:latest",
            network="host",     # Use host network to allow local addresses
            command=cmd) as container:

            # Wait for successful connection
            for log in container.logs(stream=True, follow=True):
                self.log.logger.debug(log.strip().decode())
                if b"Bootstrapped 100% (done): Done" in log:

                    # Fetch service address
                    status, result = container.exec_run("cat /var/lib/tor/hidden_service/hostname")
                    if status == 0:
                        self.log.info("Connected, serving %s:%i at %s", lhost, lport, result.decode())
                    else:
                        raise Exception(result)
