from lets.__module__ import Module, Mount, Container

# Determine architecture
import platform
arm = platform.machine().lower().startswith("arm")


class HTTP(Module):
    """
    Proxy HTTP traffic from Ngrok.
    """
    images = ["wernight/ngrok:%s" % ("armhf" if arm else "latest")]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("lhost", type=str, help="local host")
        parser.add_argument("lport", type=int, help="local port")
        parser.add_argument("--country", type=str, help="use country code (%(default)s)",
            choices=["us", "eu", "ap", "au", "sa", "jp", "in"], default="us")
        parser.add_argument("--proxy", type=str, help="use proxy ([http|socks5]://ip:port)")

    def handle(self, input, lhost, lport, country="us", proxy=None):

        # Construct configuration file
        config  = ""
        config += "update: false\n"
        config += "web_addr: false\n"

        self.log.debug("Using country code (%s)", country)
        config += "region: %s\n" % country

        # Use proxy, if specified
        if proxy:
            self.log.debug("Connecting to proxy (%s)", proxy)
            if proxy.startswith("socks5"):
                config += "socks5_proxy: %s\n" % proxy
            elif proxy.startswith("http"):
                config += "http_proxy: %s\n" % proxy
            else:
                raise AssertionError("Invalid proxy, expecting http or socks5")

        self.log.debug("Launching reverse proxy")
        with Mount("/ngrok", "ro") as mount:

            # Write configuration file
            with mount.open("config.yml", "w") as f:
                f.write(config)

            # Launch reverse proxy
            with Container.run("wernight/ngrok:%s" % ("armhf" if arm else "latest"),
                network="host",
                user="root",
                volumes=mount.volumes,
                command="ngrok http -config /ngrok/config.yml %s:%i" % (lhost, lport),
                tty=True,
                stdin_open=True
                ) as container:

                container.interact()
