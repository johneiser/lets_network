from lets.__module__ import Module, Mount, Container
import logging


class TCP(Module):
    """
    Redirect TCP traffic over TCP.
    """
    images = [
        "local/socat",      # Cross-platform
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("lhost", type=str, nargs="?",
            help="listen on host (%(default)s)", default="0.0.0.0")
        parser.add_argument("lport", type=int, help="listen on port")
        parser.add_argument("rhost", type=str, help="connect to host")
        parser.add_argument("rport", type=int, help="connect to port")

    def handle(self, input, lhost, lport, rhost, rport):
        
        # Construct command
        cmd  = ""
        cmd += " tcp-listen:%i,bind=%s,fork,reuseaddr" % (lport, lhost)
        cmd += " tcp-connect:%s:%i" % (rhost, rport)

        # Launch redirector
        with Container.run("local/socat",
            network="host",     # Use host network to allow local addresses
            tty=True,
            stdin_open=True,
            command=cmd) as container:

            self.log.info("Redirecting TCP(%s:%i) to TCP(%s:%i)", lhost, lport, rhost, rport)
            container.interact()
