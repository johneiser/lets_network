from lets.__module__ import Module, Mount, Container, TestCase
import argparse


class Socat(Module):
    """
    Redirect traffic with socat.
        - requires two '--' before socat commands

    Example:
    > lets redirect/socat -- -- -dd -v tcp-listen:4444,fork,reuseaddr tcp-connect:127.0.0.1:4445
    """
    images = [
        "local/socat",      # Cross-platform
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("command", nargs="*", help="command(s) to provide socat")

    def handle(self, input, command=None):
        
        # Launch redirector
        with Container.run("local/socat",
            network="host",     # Use host network to allow local addresses
            tty=True,
            stdin_open=True,
            entrypoint="socat",
            command=command) as container:

            # Print any missed logs
            self.log.logger.info(container.logs().decode())

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
