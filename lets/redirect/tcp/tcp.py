from lets.__module__ import Module, Mount, Container, TestCase
import logging


class TCP(Module):
    """
    Redirect TCP traffic over TCP.
    """
    images = [
        "local/socat:1.0.1",      # Cross-platform
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
        cmd  = "socat"
        cmd += " tcp-listen:%i,bind=%s,fork,reuseaddr" % (lport, lhost)
        cmd += " tcp-connect:%s:%i" % (rhost, rport)

        # Launch redirector
        with Container.run("local/socat:1.0.1",
            network="host",     # Use host network to allow local addresses
            tty=True,
            stdin_open=True,
            command=cmd) as container:

            self.log.info("Redirecting TCP(%s:%i) to TCP(%s:%i)", lhost, lport, rhost, rport)
            container.interact()

class TCPTestCase(TestCase):
    images = ["local/socat:1.0.1"]

    def test_images(self):
        """
        Test that required images work on the given architecture.
        """
        import platform
        output = b""
        image = "local/socat:1.0.1"
        with Container.run(image, command="socat -h") as container:
            output = container.output()

        self.assertRegex(output, b"Usage:",
            "Image (%s) failed for architecture: %s" % (image, platform.machine()))
