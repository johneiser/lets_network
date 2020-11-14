from lets.__module__ import Module, Mount, Container, TestCase
import argparse

# Determine architecture
import platform
machine = platform.machine().lower()
arm = machine.startswith("arm") or machine.startswith("aarch")


class Http(Module):
    """
    Proxy HTTP traffic.
    """
    images = ["mitmproxy/mitmproxy:%s" % ("5.0.1-ARMv7" if arm else "5.0.1")]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-p", "--port", type=int, help="listen on port", default=8080)
        parser.add_argument("--interface", type=str, help="listen on interface", default="0.0.0.0")
        parser.add_argument("-m", "--mitm", action="store_true", help="mitm proxied traffic")
        parser.add_argument("-c", "--ca", type=argparse.FileType("rb"), help="mitm certificate authority (PEM key+cert)")

    def handle(self, input, port=8080, interface="0.0.0.0", mitm=False, ca=None):

        with Mount("/root/.mitmproxy") as mount:

            # Write certificate authority
            if ca:
                self.log.debug("Writing certificate authority (%s)", ca.name)
                with mount.open("mitmproxy-ca.pem", "wb") as f:
                    f.write(ca.read())
            
            # Construct command
            if mitm:
                cmd  = "/usr/bin/mitmproxy"             # Bypass entrypoint to mount CA
                cmd += " --anticomp --anticache -k"     # Maximize request exposure
                cmd += " --mode regular"
                cmd += " --listen-host %s" % interface
                cmd += " --listen-port %i" % port
            else:
                cmd  = "/usr/bin/mitmdump"      # Bypass entrypoint to mount CA
                cmd += " --ignore-hosts .*"     # Disable TLS intercept
                cmd += " --mode regular"
                cmd += " --listen-host %s" % interface
                cmd += " --listen-port %i" % port

            # Launch proxy
            self.log.debug("Launching proxy server")
            with Container.run("mitmproxy/mitmproxy:%s" % ("5.0.1-ARMv7" if arm else "5.0.1"),
                network="host",     # Use host network to enable local addresses
                tty=True,
                stdin_open=True,
                volumes=mount.volumes,
                command=cmd) as container:

                self.log.info("Proxy server listening at http://%s:%i", interface, port)
                container.interact() if mitm else container.wait()

class HttpTestCase(TestCase):
    images = ["mitmproxy/mitmproxy:%s" % ("5.0.1-ARMv7" if arm else "5.0.1")]

    def test_images(self):
        """
        Test that required images work on the given architecture.
        """
        output = b""
        with Container.run("mitmproxy/mitmproxy:%s" % ("5.0.1-ARMv7" if arm else "5.0.1"),
            command="mitmproxy -h") as container:
            output = container.output()

        self.assertRegex(output, b"usage: mitmproxy", "Container failed for architecture: %s" % platform.machine())
