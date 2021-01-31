from lets.__module__ import Module, Container, TestCase
import os


class HTTP(Module):
    """
    Serve a local directory over HTTP.
    """
    images = [
        "nginx:latest",     # Cross-platform
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("directory", type=str, nargs="?",
            help="local directory to serve (current)")
        parser.add_argument("-p", "--port", type=int, default=80,
            help="listen on port (%(default)i)")
        parser.add_argument("--interface", type=str, default="0.0.0.0",
            help="listen on interface (%(default)s)")

    def handle(self, input, directory=None, port=80, interface="0.0.0.0"):

        # Validate directory
        if not directory: directory = os.getcwd()
        assert os.path.isdir(directory), "Invalid directory: %s" % directory
        self.log.info("Serving %s at %s:%i", os.path.abspath(directory), interface, port)

        # Launch nginx
        with Container.run("nginx:latest",
            ports={"80/tcp" : (interface, port)},
            volumes={os.path.abspath(directory) : {
                "bind"  : "/usr/share/nginx/html",
                "mode"  : "ro",
            }}) as container:

                for log in container.logs(stream=True, follow=True):
                    self.log.logger.debug(log.strip().decode())

class HTTPTestCase(TestCase):
    images = [
        "nginx:latest",
        ]

    def test_images(self):
        """
        Test that required images work on the given architecture.
        """
        import platform
        output = b""
        image = "nginx:latest"
        with Container.run(image, command="nginx -h") as container:
            output = container.output()

        self.assertRegex(output, b"Usage:",
            "Image (%s) failed for architecture: %s" % (image, platform.machine()))
