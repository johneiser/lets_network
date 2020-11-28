from lets.__module__ import Module, IterWriter
from scapy.all import conf, raw, AsyncSniffer, PcapWriter
from scapy.error import Scapy_Exception
import re


class LAN(Module):
    """
    Sniff packets on a local area network.
    """
    # Prevent newlines when generating
    delimiter = b""
    
    # Global variables
    pcap    = None
    regex   = None
    xregex  = None
    debug   = False

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-n", "--interface", action="append",
            help="network interface(s) on which to sniff)")
        parser.add_argument("-c", "--count", type=int, default=0,
            help="number of packets to sniff (all)")
        parser.add_argument("-t", "--timeout", type=int, default=None,
            help="number of seconds to sniff (infinite)")
        parser.add_argument("-f", "--filter", type=str,
            help="BPF filter to apply")
        parser.add_argument("-r", "--regex", type=str, action="append", default=[],
            help="expression(s) to qualify packet (AND)")
        parser.add_argument("-x", "--xregex", type=str, action="append", default=[],
            help="expression(s) to disqualify packet (OR)")
        parser.add_argument("-m", "--monitor", action="store_true",
            help="listen in monitor mode (False)")
        parser.add_argument("-p", "--pcap", action="store_true",
            help="output packets as pcap (False)")
        parser.add_argument("-d", "--debug", action="store_true",
            help="unpack and display each captured packet")

    def handle(self, input, interface=None, count=0, timeout=None, filter=None, regex=None, xregex=None, monitor=False, pcap=False, debug=False):
        self.debug = debug

        # Compile expressions
        if regex:  self.regex  = [re.compile(r.encode(), re.DOTALL|re.MULTILINE) for r in list(regex)]
        if xregex: self.xregex = [re.compile(x.encode(), re.DOTALL|re.MULTILINE) for x in list(xregex)]

        # Output pcap to infinitely iterable file
        with IterWriter() as output:
            if pcap:
                self.pcap = PcapWriter(output, sync=True)
            
            # Configure sniffer and produce sniffer stream
            try:
                stream = AsyncSniffer(
                    started_callback = lambda: self.log.info("Sniffing interface(s): %s...", interface or conf.iface),
                    iface   = interface or conf.iface,
                    count   = count,
                    timeout = timeout,
                    filter  = filter,
                    lfilter = self._lfilter,
                    prn     = self._prn,
                    store   = False,
                    monitor = monitor,
                    )
                
                # Start sniffer stream
                stream.start()
                
                # Output pcap data
                if pcap:
                    for data in output:
                        yield data
                        if not stream.running and not output.closed:
                            output.close()

                # Wait for stream to complete
                stream.join()

            except Scapy_Exception as e:
                self.log.error(e)

    def _prn(self, pkt):
        """
        Handle captured packet.

        :param object pkt: captured packet
        """
        # Show packet summary
        self.log.logger.debug(pkt.summary())

        # Show packet details
        if self.debug:
            self.log.logger.info(pkt.show(dump=True))

        # Output full pcap
        if self.pcap:
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
