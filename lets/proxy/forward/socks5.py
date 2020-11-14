from lets.__module__ import Module, Mount, Container
import argparse

# Determine architecture
import platform
arm = platform.machine().lower().startswith("arm")


class Socks5(Module):
    """
    Proxy SOCKS5 traffic.
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
                cmd += " --mode socks5 --showhost"
                cmd += " --listen-host %s" % interface
                cmd += " --listen-port %i" % port
            else:
                cmd  = "/usr/bin/mitmdump"      # Bypass entrypoint to mount CA
                cmd += " --ignore-hosts .*"     # Disable TLS intercept
                cmd += " --mode socks5 --showhost"
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
