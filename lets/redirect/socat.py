from lets.__module__ import Module, Mount, Container
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