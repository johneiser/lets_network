from lets.__module__ import Module, Mount, Container, TestCase


class DNS(Module):
    """
    Provide a simple DNS service (with /etc/hosts from input).

    For example:

    $ echo "1.2.3.4 my.domain" | lets listen/serve/dns -u 1.1.1.1
    """
    images = [
        "local/dnsmasq:1.0.0",      # Cross-platform
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-p", "--port", type=int, default=53,
            help="listen on port (%(default)i)")
        parser.add_argument("--interface", type=str, default="0.0.0.0",
            help="listen on interface (%(default)s)")
        parser.add_argument("-u", "--upstream", type=str, action="append",
            help="forward requests to upstream DNS servers")
        parser.add_argument("-c", "--cache", type=int, default=150,
            help="specify cache size (150 names)")

    def handle(self, input, port=53, interface="0.0.0.0", upstream=None, cache=150):

        with Mount("/data") as mount:

            # Construct command
            cmd  = "dnsmasq -C /data/dnsmasq.conf -d"

            # Write configuration
            with mount.open("dnsmasq.conf", "w") as f:
                f.write("port=%i\n" % port)
                f.write("listen-address=%s\n" % interface)
                f.write("bind-interfaces\n")
                f.write("log-queries\n")
                f.write("cache-size=%i\n" % cache)
                
                # Add upstream servers
                f.write("no-resolv\n")      # Don't read /etc/resolv.conf
                if upstream:
                    if not isinstance(upstream, list):
                        upstream = [upstream]
                    for server in upstream:
                        f.write("server=%s\n" % server)
                
                # Add hosts
                f.write("no-hosts\n")       # Don't read /etc/hosts
                if input:
                    f.write("addn-hosts=/data/hosts\n")
                    with mount.open("hosts", "wb") as h:
                        for data in input:
                            h.write(data)

            # Launch dnsmasq
            with Container.run("local/dnsmasq:1.0.0",
                stdin_open=True,
                tty=True,
                network="host",
                volumes=mount.volumes,
                command=cmd) as container:

                container.interact()

class DNSTestCase(TestCase):
    images = ["local/dnsmasq:1.0.0"]

    def test_images(self):
        """
        Test that required images work on the given architecture.
        """
        import platform
        output = b""
        image = "local/dnsmasq:1.0.0"
        with Container.run(image, command="dnsmasq --help") as container:
            output = container.output()

        self.assertRegex(output, b"Usage: dnsmasq",
            "Image (%s) failed for architecture: %s" % (image, platform.machine()))
