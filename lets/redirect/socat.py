from lets.__module__ import Module, Mount, Container, TestCase
import argparse


class Socat(Module):
    """
    Redirect traffic with socat.
    """
    images = [
        "local/socat",      # Cross-platform
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("command", nargs=argparse.REMAINDER,
            help="command to provide socat")

    def handle(self, input, command):
        
        # Launch redirector
        with Container.run("local/socat",
            network="host",     # Use host network to allow local addresses
            tty=True,
            stdin_open=True,
            command=command) as container:

            container.interact()

class SocatTestCase(TestCase):
    images = ["local/socat"]

    def test_images(self):
        """
        Test that required images work on the given architecture.
        """
        import platform

        output = b""
        image = "local/socat"
        with Container.run(image, command="-h") as container:
            output = container.output()

        self.assertRegex(output, b"Usage:",
            "Image (%s) failed for architecture: %s" % (image, platform.machine()))
