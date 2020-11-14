from lets.__module__ import Module, Mount, Container, TestCase
import argparse

# Determine architecture
import platform
machine = platform.machine().lower()
arm = machine.startswith("arm") or machine.startswith("aarch")


class HTTP(Module):
    """
    Proxy HTTP traffic over TOR.
    """
    images = [
        "dperson/torproxy:latest",      # Cross-platform, no versions
        "mitmproxy/mitmproxy:%s" % ("5.0.1-ARMv7" if arm else "5.0.1"),
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-p", "--port", type=int, help="listen on port", default=8080)
        parser.add_argument("--interface", type=str, help="listen on interface", default="0.0.0.0")
        parser.add_argument("--country", type=str, help="emerge from country code")
        parser.add_argument("-m", "--mitm", action="store_true", help="mitm proxied traffic")
        parser.add_argument("-c", "--ca", type=argparse.FileType("rb"), help="mitm certificate authority (PEM key+cert)")

    def handle(self, input, port=8080, interface="0.0.0.0", country=None, mitm=False, ca=None):

        # Construct command
        cmd = ""

        if country:
            self.log.info("Using country code: %s", country)
            cmd += " -l %s" % country

        # Launch tor
        self.log.info("Connecting to tor...")
        with Container.run("dperson/torproxy:latest",
            ports={"8080/tcp" : (interface, port)},
            command=cmd) as vpn:
           
            # Wait for successful connection
            for log in vpn.logs(stream=True, follow=True):
                self.log.logger.debug(log.strip().decode())
                if b"Bootstrapped 100% (done): Done" in log:
                    self.log.info("Connected to tor")
                    break

            with Mount("/root/.mitmproxy") as mount:

                # Write certificate authority
                if ca:
                    self.log.debug("Writing certificate authority (%s)", ca.name)
                    with mount.open("mitmproxy-ca.pem", "wb") as f:
                        f.write(ca.read())

                # Construct command
                if mitm:
                    cmd  = "/usr/bin/mitmproxy"             # Bypass entrypoint to mount CA
                    cmd += " --anticomp --anticache -k"     # Maximimze request exposure
                    cmd += " --mode upstream:http://127.0.0.1:8118"
                    cmd += " --listen-host 0.0.0.0"         
                    cmd += " --listen-port 8080"
                else:
                    cmd  = "/usr/bin/mitmdump"      # Bypass entrypoint to mount CA
                    cmd += " --ignore-hosts .*"     # Disable TLS intercept
                    cmd += " --mode upstream:http://127.0.0.1:8118"
                    cmd += " --listen-host 0.0.0.0"
                    cmd += " --listen-port 8080"

                # Launch proxy
                self.log.debug("Launching proxy server")
                with Container.run("mitmproxy/mitmproxy:%s" % ("5.0.1-ARMv7" if arm else "5.0.1"),
                    network_mode="container:%s" % vpn.name,
                    tty=True,
                    stdin_open=True,
                    volumes=mount.volumes,
                    command=cmd) as proxy:

                    self.log.info("Proxy server listening at http://%s:%i", interface, port)
                    proxy.interact() if mitm else proxy.wait()

class HttpTestCase(TestCase):
    images = ["dperson/torproxy:latest"]

    def test_images(self):
        """
        Test that required images work on the given architecture.
        """
        output = b""
        image = "dperson/torproxy:latest"
        with Container.run(image, command="-h") as container:
            output = container.output()

        self.assertRegex(output, b"Usage: ",
            "Image (%s) failed for architecture: %s" % (image, platform.machine()))
