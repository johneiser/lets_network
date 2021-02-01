from lets.__module__ import Module, Mount, Container
import argparse


class TCP(Module):
    """
    Redirect TLS traffic over TCP.
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
        parser.add_argument("-k", "--key", type=argparse.FileType("rb"),
            help="use TLS key")
        parser.add_argument("-c", "--certificate", type=argparse.FileType("rb"),
            help="use TLS certificate")
        parser.add_argument("--ca", type=argparse.FileType("rb"),
            help="use TLS certificate authority to verify peer")
        parser.add_argument("--version", type=str, choices=["tls1", "tls1.1", "tls1.2"],
            help="use specific TLS version")

    def handle(self, input, lhost, lport, rhost, rport, key=None, certificate=None, ca=None, version=None):

        with Mount("/data", "ro") as mount:

            # Construct command
            cmd  = "socat"
            cmd += " openssl-listen:%i,bind=%s,fork,reuseaddr" % (lport, lhost)
            cmd += ",key=/data/key.pem,cert=/data/cert.pem"
            if version:
                self.log.debug("Using version: %s", version)
                cmd += ",method=%s" % version

            # Write supplied TLS key/certificate
            if key and certificate:
                self.log.debug("Using key: %s", key.name)
                with mount.open("key.pem", "wb") as f:
                    f.write(key.read())
                self.log.debug("Using certificate: %s", certificate.name)
                with mount.open("cert.pem", "wb") as f:
                    f.write(certificate.read())
            
            # Write generated TLS key/certificate
            else:
                if key:
                    self.log.warning("Missing certificate, using self-signed")
                if certificate:
                    self.log.warning("Missing key, using self-signed")

                self.log.debug("Generating self-signed certificate")
                import lets.generate.tls.certificate
                pem = lets.generate.tls.certificate()
                with mount.open("key.pem", "wb") as f:
                    f.write(pem)
                with mount.open("cert.pem", "wb") as f:
                    f.write(pem)
            
            # Write certificate authority
            if ca:
                self.log.debug("Verifying peer with certificate: %s", ca.name)
                with mount.open("ca.pem", "wb") as f:
                    f.write(ca.read())
                cmd += ",cafile=/data/ca.pem"
            else:
                cmd += ",verify=0"

            cmd += " tcp-connect:%s:%i" % (rhost, rport)

            # Launch redirector
            with Container.run("local/socat:1.0.1",
                network="host",     # Use host network to allow local addresses
                tty=True,
                stdin_open=True,
                volumes=mount.volumes,
                command=cmd) as container:

                self.log.info("Redirecting TLS(%s:%i) to TCP(%s:%i)", lhost, lport, rhost, rport)
                container.interact()
