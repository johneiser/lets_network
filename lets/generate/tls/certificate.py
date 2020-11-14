from lets.__module__ import Module
import random
from OpenSSL import crypto


class Certificate(Module):
    """
    Generate an SSL/TLS X.509 certificate in PEM format (provide certificate authority as input).
    """

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-s", "--size", type=int,
            help="key size (%(default)i bits)", default=2048)
        parser.add_argument("-e", "--expire", type=int,
            help="expire time (%(default)i days)", default=365)
        parser.add_argument("-a", "--authority", action="store_true",
            help="indicate certificate authority (%(default)s)")
        
        parser.add_argument("--country", type=str,
            help="country name (%(default)s)", default="AU")
        parser.add_argument("--state", type=str,
            help="state (%(default)s)", default="Some-State")
        parser.add_argument("--locality", type=str,
            help="locality (%(default)s)")
        parser.add_argument("--organization", type=str,
            help="organization (%(default)s)", default="Internet Widgets Pty Ltd")
        parser.add_argument("--organizational-unit", type=str,
            help="organizational unit (%(default)s)")
        parser.add_argument("-n", "--common-name", type=str,
            help="common name (%(default)s)")
        parser.add_argument("--email", type=str,
            help="email (%(default)s)")

    def handle(self, input, size=2048, expire=365, authority=False,
            country="AU", state="Some-State", locality=None, organization="Internet Widgets Pty Ltd", organizational_unit=None, common_name=None, email=None):
        
        # Load certificate authority
        for data in input or [None]:
            ca_key  = None
            ca_cert = None
            ca_subj = None
            if data:
                try:
                    ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, data)
                    ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, data)
                    ca_subj = ca_cert.get_subject()
                    self.log.debug("Loading certificate authority (%s)", ca_subj.O)
                except crypto.Error as e:
                    self.log.exception("Invalid certificate authority")
                    continue

            # Generate private key
            self.log.debug("Generating private key (%i bits)", size)
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, size)

            # Generate certificate
            self.log.debug("Generating certificate (valid %i days)", expire)
            cert = crypto.X509()
            cert.set_version(2)
            cert.set_serial_number(random.randint(50000000, 100000000))
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(expire*24*60*60)
            subj = cert.get_subject()
            if country:             subj.C = country
            if state:               subj.ST = state
            if locality:            subj.L = locality
            if organization:        subj.O = organization
            if organizational_unit: subj.OU = organizational_unit
            if common_name:         subj.CN = common_name
            if email:               subj.emailAddress = email
            cert.set_issuer(ca_subj or subj)
            cert.set_pubkey(key)
        
            # Define certificate behavior
            if authority:
                cert.add_extensions([
                    crypto.X509Extension(b"basicConstraints", True, b"CA:TRUE"),
                    crypto.X509Extension(b"keyUsage", True, b"keyCertSign, cRLSign"),
                    ])
            else:
                cert.add_extensions([
                    crypto.X509Extension(b"basicConstraints", False, b"CA:FALSE"),
                    crypto.X509Extension(b"keyUsage", False, b"digitalSignature, keyAgreement"),
                    crypto.X509Extension(b"extendedKeyUsage", False, b"clientAuth, serverAuth"),
                    ])

            # Supply certificate identifiers
            cert.add_extensions([
                crypto.X509Extension(b"subjectKeyIdentifier",
                    False, b"hash", subject=cert),
                ])
            if ca_cert:
                cert.add_extensions([
                    crypto.X509Extension(b"authorityKeyIdentifier",
                        False, b"keyid:always", issuer=ca_cert),
                    ])

            # Sign certificate
            if ca_key:
                self.log.debug("Signing certificate with certificate authority")
                cert.sign(ca_key, "sha256")
            else:
                self.log.debug("Self-signing certificate")
                cert.sign(key, "sha256")

            yield (crypto.dump_privatekey(crypto.FILETYPE_PEM, key) + 
                crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

