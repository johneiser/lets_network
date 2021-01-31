from lets.__module__ import Module, Mount, Container, TestCase, IterReader, IterSync
from scapy.all import raw, AsyncSniffer, PcapWriter
from scapy.error import Scapy_Exception
import re


class Termshark(Module):
    """
    Analyze a pcap file using termshark.
    """
    images = [
        "local/termshark:1.0.0",    # Cross-platform
        ]

    # Global variables
    regex   = None
    xregex  = None

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-c", "--count", type=int, default=0,
            help="number of packets to read (all)")
        parser.add_argument("-t", "--timeout", type=int, default=None,
            help="number of seconds to read (infinite)")
        parser.add_argument("-f", "--filter", type=str,
            help="BPF filter to apply")
        parser.add_argument("-r", "--regex", type=str, action="append", default=[],
            help="expression(s) to qualify packet (AND)")
        parser.add_argument("-x", "--xregex", type=str, action="append", default=[],
            help="expression(s) to disqualify packet (OR)")

    def handle(self, input, count=0, timeout=None, filter=None, regex=None, xregex=None):
        assert input is not None, "Must provide pcap as input"

        # Compile expressions
        if regex:  self.regex  = [re.compile(r.encode(), re.DOTALL|re.MULTILINE) for r in list(regex)]
        if xregex: self.xregex = [re.compile(x.encode(), re.DOTALL|re.MULTILINE) for x in list(xregex)]

        with Mount("/data") as mount:

            # Prepare pcap file for input
            with mount.open("input.pcap", "wb", buffering=0) as f:
                self.pcap = PcapWriter(f, sync=True)

                # Route pcap data from synchronized input as readable file
                with IterReader(IterSync(input)) as ifile:

                    # Configure sniffer and produce sniffer stream
                    try:
                        stream = AsyncSniffer(
                            offline = ifile,    # Read from virtual file
                            count   = count,
                            timeout = timeout,
                            filter  = filter,
                            lfilter = self._lfilter,
                            prn     = self._prn,
                            store   = False)

                        # Start sniffer stream
                        stream.start()

                        # Launch termshark
                        with Container.run("local/termshark:1.0.0",
                            stdin_open=True,
                            tty=True,
                            volumes=mount.volumes,
                            command="termshark -r /data/input.pcap") as container:

                            container.interact()

                        # Wait for sniffer stream to finish
                        stream.join()

                    except Scapy_Exception as e:
                        self.log.error(e)

    def _prn(self, pkt):
        """
        Handle captured packet.

        :param object pkt: captured packet
        """
        # Write to pcap file
        self.pcap.write(pkt)

    def _lfilter(self, pkt):
        """
        Assess potential packet for capture.

        :param object pkt: potential packet
        :return: whether to capture packet
        :rtype: bool
        """
        # Check xregex are excluded (OR)
        if self.xregex:
            for x in self.xregex:
                if x.search(raw(pkt)):
                    return False

        # Check regex are included (AND)
        if self.regex:
            for r in self.regex:
                if not r.search(raw(pkt)):
                    return False

        return True

class TermsharkTestCase(TestCase):
    images = ["local/termshark:1.0.0"]

    def test_images(self):
        """
        Test that required images work on the given architecture.
        """
        import platform
        output = b""
        image = "local/termshark:1.0.0"
        with Container.run(image, command="termshark -h") as container:
            output = container.output()

        self.assertRegex(output, b"Usage:",
            "Image (%s) failed for architecture: %s" % (image, platform.machine()))
