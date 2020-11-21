from lets.__module__ import Module, Mount, Container
import argparse


class TCP(Module):
    """
    Redirect TLS traffic over TCP.
    """
    images = [
        "local/socat:1.0.0",      # Cross-platform
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

    def handle(self, input, lhost, lport, rhost, rport, key=None, certificate=None):

        with Mount("/certs", "ro") as mount:

            # Write supplied TLS key/certificate
            if key and certificate:
                with mount.open("key.pem", "wb") as f:
                    f.write(key.read())
                with mount.open("cert.pem", "wb") as f:
                    f.write(certificate.read())
            
            # Write generated TLS key/certificate
            else:
                if key:
                    self.log.warning("Missing certificate")
                if certificate:
                    self.log.warning("Missing key")

                self.log.debug("Generating self-signed certificate")
                import lets.generate.tls.certificate
                pem = lets.generate.tls.certificate()
                with mount.open("key.pem", "wb") as f:
                    f.write(pem)
                with mount.open("cert.pem", "wb") as f:
                    f.write(pem)

            # Construct command
            cmd  = ""
            cmd += " openssl-listen:%i,bind=%s,fork,reuseaddr" % (lport, lhost)
            cmd += ",key=/certs/key.pem,cert=/certs/cert.pem,verify=0"
            cmd += " tcp-connect:%s:%i" % (rhost, rport)

            # Launch redirector
            with Container.run("local/socat:1.0.0",
                network="host",     # Use host network to allow local addresses
                tty=True,
                stdin_open=True,
                volumes=mount.volumes,
                command=cmd) as container:

                self.log.info("Redirecting TLS(%s:%i) to TCP(%s:%i)", lhost, lport, rhost, rport)
                container.interact()
