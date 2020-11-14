from lets.__module__ import Module, Mount, Container
import os, argparse

# Determine architecture
import platform
machine = platform.machine().lower()
arm = machine.startswith("arm") or machine.startswith("aarch")


class Socks5(Module):
    """
    Proxy SOCKS5 traffic over an OpenVPN tunnel (provide vpn config as input).
    """
    images = [
        "dperson/openvpn-client:latest",        # Cross-platform, no versions
        "mitmproxy/mitmproxy:%s" % ("5.0.1-ARMv7" if arm else "5.0.1"),
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-p", "--port", type=int, help="listen on port", default=8080)
        parser.add_argument("--interface", type=str, help="listen on interface", default="0.0.0.0")
        parser.add_argument("-a", "--auth", type=argparse.FileType("rb"), help="use openvpn authentication file")
        parser.add_argument("-m", "--mitm", action="store_true", help="mitm proxied traffic")
        parser.add_argument("-c", "--ca", type=argparse.FileType("rb"), help="mitm certificate authority (PEM key+cert)")

    def handle(self, input, port=8080, interface="0.0.0.0", auth=None, mitm=False, ca=None):
        assert input is not None, "Must provide OpenVPN configuration as input"

        # Retrieve OpenVPN configuration
        for data in input:

            with Mount("/vpn", "ro") as mount:

                # Write OpenVPN configuration
                self.log.debug("Writing access configuration")
                with mount.open("vpn.conf", "wb") as f:
                    f.write(data)

                # Write OpenVPN authentication
                if auth:
                    self.log.debug("Writing authentication file (%s)", auth.name)
                    with mount.open(os.path.basename(auth.name), "wb") as f:
                        f.write(auth.read())

                # Launch tunnel
                self.log.info("Connecting to tunnel...")
                with Container.run("dperson/openvpn-client:latest",
                    cap_add=["NET_ADMIN"],
                    devices=["/dev/net/tun"],
                    ports={"%i/tcp" % port : (interface, port)},
                    volumes=mount.volumes) as vpn:

                    # Wait for successful connection
                    for log in vpn.logs(stream=True, follow=True):
                        self.log.logger.debug(log.strip().decode())
                        if b"Initialization Sequence Complete" in log:
                            self.log.info("Connected to tunnel (%s)", vpn.name)
                            break

                    with Mount("/root/.mitmproxy") as certs:

                        # Write certificate authority to privileged directory
                        if ca:
                            self.log.debug("Writing certificate authority (%s)", ca.name)
                            with certs.open("mitmproxy-ca.pem", "wb") as f:
                                f.write(ca.read())

                        # Construct command
                        if mitm:
                            cmd  = "/usr/bin/mitmproxy"             # Bypass entrypoint to mount CA
                            cmd += " --anticomp --anticache -k"     # Maximize request exposure
                            cmd += " --mode socks5 --showhost"
                            cmd += " --listen-host 0.0.0.0"
                            cmd += " --listen-port %i" % port
                        else:
                            cmd  = "/usr/bin/mitmdump"      # Bypass entrypoint to mount CA
                            cmd += " --ignore-hosts .*"     # Disable TLS intercept
                            cmd += " --mode socks5 --showhost"
                            cmd += " --listen-host 0.0.0.0"
                            cmd += " --listen-port %i" % port
                    
                        # Launch proxy
                        with Container.run("mitmproxy/mitmproxy:%s" % ("5.0.1-ARMv7" if arm else "5.0.1"),
                            network_mode="container:%s" % vpn.name,
                            tty=True,
                            stdin_open=True,
                            volumes=certs.volumes,
                            command=cmd) as proxy:

                            self.log.info("Proxy server listening at http://%s:%i", interface, port)
                            proxy.interact() if mitm else proxy.wait()
