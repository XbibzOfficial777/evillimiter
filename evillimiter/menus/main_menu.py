import time
import socket
import curses
import netaddr
import threading
import collections
from terminaltables import SingleTable

import evillimiter.console.shell as shell
import evillimiter.networking.utils as netutils
from evillimiter.networking import persist as persist_module
from evillimiter.common import config as ev_config
from .menu import CommandMenu
from evillimiter.networking.utils import BitRate
from evillimiter.console.io import IO
from evillimiter.console.prompt import PromptManager
from evillimiter.console.chart import BarChart, LiveGraph
from evillimiter.console.banner import get_main_banner
from evillimiter.networking.host import Host
from evillimiter.networking.limit import Limiter, Direction
from evillimiter.networking.spoof import ARPSpoofer, NDPSpoofer
from evillimiter.networking.scan import HostScanner
from evillimiter.networking.monitor import BandwidthMonitor
from evillimiter.networking.watch import HostWatcher
from evillimiter.networking.flap import Flapper


class MainMenu(CommandMenu):
    def __init__(self, version: str, interface: str, gateway_ip: str, gateway_mac: str, netmask: str, initial_hosts: list | None = None, ndp_spoofer: NDPSpoofer | None = None, config: dict | None = None) -> None:
        super().__init__()
        self._selected_host: Host | None = None
        self.ndp_spoofer = ndp_spoofer
        self.prompt = f'{IO.Style.BRIGHT}Main{IO.Style.RESET_ALL} >>> '
        self.parser.add_subparser('clear', self._clear_handler)

        hosts_parser = self.parser.add_subparser('hosts', self._hosts_handler)
        hosts_parser.add_flag('--force', 'force')

        scan_parser = self.parser.add_subparser('scan', self._scan_handler)
        scan_parser.add_parameterized_flag('--range', 'iprange')

        limit_parser = self.parser.add_subparser('limit', self._limit_handler)
        limit_parser.add_parameter('id')
        limit_parser.add_parameter('rate')
        limit_parser.add_flag('--upload', 'upload')
        limit_parser.add_flag('--download', 'download')

        block_parser = self.parser.add_subparser('block', self._block_handler)
        block_parser.add_parameter('id')
        block_parser.add_flag('--upload', 'upload')
        block_parser.add_flag('--download', 'download')

        free_parser = self.parser.add_subparser('free', self._free_handler)
        free_parser.add_parameter('id')

        self.parser.add_subparser('blockall', self._block_all_handler)
        self.parser.add_subparser('unblockall', self._unblock_all_handler)

        graph_parser = self.parser.add_subparser('graph', self._graph_handler)
        graph_parser.add_parameterized_flag('--interval', 'interval')
        graph_parser.add_parameterized_flag('--duration', 'duration')

        add_parser = self.parser.add_subparser('add', self._add_handler)
        add_parser.add_parameter('ip')
        add_parser.add_parameterized_flag('--mac', 'mac')

        monitor_parser = self.parser.add_subparser('monitor', self._monitor_handler)
        monitor_parser.add_parameter('id', required=False)
        monitor_parser.add_parameterized_flag('--interval', 'interval')

        analyze_parser = self.parser.add_subparser('analyze', self._analyze_handler)
        analyze_parser.add_parameter('id')
        analyze_parser.add_parameterized_flag('--duration', 'duration')

        watch_parser = self.parser.add_subparser('watch', self._watch_handler)
        watch_add_parser = watch_parser.add_subparser('add', self._watch_add_handler)
        watch_add_parser.add_parameter('id')
        watch_remove_parser = watch_parser.add_subparser('remove', self._watch_remove_handler)
        watch_remove_parser.add_parameter('id')
        watch_set_parser = watch_parser.add_subparser('set', self._watch_set_handler)
        watch_set_parser.add_parameter('attribute')
        watch_set_parser.add_parameter('value')

        flap_parser = self.parser.add_subparser('flap', self._flap_handler)
        flap_parser.add_parameter('id')
        flap_parser.add_parameterized_flag('--block', 'block_time')
        flap_parser.add_parameterized_flag('--free', 'free_time')

        history_parser = self.parser.add_subparser('history', self._history_handler)

        refresh_parser = self.parser.add_subparser('refresh', self._refresh_handler)

        sort_parser = self.parser.add_subparser('sort', self._sort_handler)
        sort_parser.add_parameter('field')

        select_parser = self.parser.add_subparser('select', self._select_handler)
        select_parser.add_parameter('id')

        self.parser.add_subparser('selected', self._selected_handler)
        self.parser.add_subparser('back', self._back_handler)

        self.parser.add_subparser('help', self._help_handler)
        self.parser.add_subparser('?', self._help_handler)

        self.parser.add_subparser('debug', self._debug_handler)

        self.parser.add_subparser('quit', self._quit_handler)
        self.parser.add_subparser('exit', self._quit_handler)

        self.version = version          # application version
        self.interface = interface      # specified IPv4 interface
        self.gateway_ip = gateway_ip 
        self.gateway_mac = gateway_mac
        self.netmask = netmask

        # range of IP address calculated from gateway IP and netmask
        self.iprange = list(netaddr.IPNetwork(f'{self.gateway_ip}/{self.netmask}'))

        self.host_scanner = HostScanner(self.interface, self.iprange)
        self.arp_spoofer = ARPSpoofer(self.interface, self.gateway_ip, self.gateway_mac)
        self.limiter = Limiter(self.interface)
        self.bandwidth_monitor = BandwidthMonitor(self.interface, 1)
        self.host_watcher = HostWatcher(self.host_scanner, self._reconnect_callback)
        self.flapper = Flapper(self.limiter)

        # holds discovered hosts
        self.hosts = initial_hosts if initial_hosts is not None else []
        self.hosts_lock = threading.Lock()

        # set up enhanced prompt with tab completion, history, auto-suggest
        pm = PromptManager(get_hosts_fn=lambda: self.hosts if hasattr(self, 'hosts') else [])
        IO.set_prompt_manager(pm)
        pm.history_store.clear()

        self.config = config or {}
        if self.config.get('autosave_limits', True) and self.hosts:
            reapplied = persist_module.reapply_limits(self.hosts, self.limiter, self.arp_spoofer, self.bandwidth_monitor, self.ndp_spoofer)
            if reapplied > 0:
                IO.ok(f'{reapplied} persistent limit(s) reapplied.')

        self._print_help_reminder()

        # start the spoof threads
        self.arp_spoofer.start()
        if self.ndp_spoofer:
            self.ndp_spoofer.start()
        # start the bandwidth monitor thread
        self.bandwidth_monitor.start()
        # start the host watch thread
        self.host_watcher.start()

    def interrupt_handler(self, ctrl_c: bool = True) -> None:
        if ctrl_c:
            IO.spacer()

        IO.ok('cleaning up... stand by...')

        self.flapper.stop_all()

        for host in self.hosts:
            self.limiter.unlimit(host, Direction.BOTH)
            if host.spoofed:
                self.arp_spoofer.remove(host)
                self.bandwidth_monitor.remove(host)
                self.host_watcher.remove(host)
                if self.ndp_spoofer:
                    self.ndp_spoofer.remove(host)

        self.arp_spoofer.stop()
        if self.ndp_spoofer:
            self.ndp_spoofer.stop()
        self.bandwidth_monitor.stop()

    def _scan_handler(self, args) -> None:
        if args.iprange:
            iprange = self._parse_iprange(args.iprange)
            if iprange is None:
                IO.error('invalid ip range.')
                return
        else:
            iprange = None

        with self.hosts_lock:
            for host in self.hosts:
                self._free_host(host)
            
        IO.spacer()
        hosts = self.host_scanner.scan(iprange)

        self.hosts_lock.acquire()
        self.hosts = hosts
        self.hosts_lock.release()

        IO.ok(f'{IO.Fore.LIGHTYELLOW_EX}{len(hosts)}{IO.Style.RESET_ALL} hosts discovered.')
        IO.spacer()

    def _hosts_handler(self, args) -> None:
        table_data: list[list[str]] = [[
            f'{IO.Style.BRIGHT}ID{IO.Style.RESET_ALL}',
            f'{IO.Style.BRIGHT}IP address{IO.Style.RESET_ALL}',
            f'{IO.Style.BRIGHT}MAC address{IO.Style.RESET_ALL}',
            f'{IO.Style.BRIGHT}IPv6{IO.Style.RESET_ALL}',
            f'{IO.Style.BRIGHT}Hostname{IO.Style.RESET_ALL}',
            f'{IO.Style.BRIGHT}Status{IO.Style.RESET_ALL}',
            f'{IO.Style.BRIGHT}Bypass{IO.Style.RESET_ALL}'
        ]]
        
        with self.hosts_lock:
            for host in self.hosts:
                ipv6_display = host.ipv6[0] if host.ipv6 else '-'
                if len(host.ipv6) > 1:
                    ipv6_display = f'{host.ipv6[0]} ...'
                suspicion = getattr(host, 'bypass_suspicion', 0)
                if suspicion == 2:
                    bypass_str = f'{IO.Fore.RED}BYPASS{IO.Style.RESET_ALL}'
                elif suspicion == 1:
                    bypass_str = f'{IO.Fore.LIGHTYELLOW_EX}WARN{IO.Style.RESET_ALL}'
                else:
                    bypass_str = '-'
                table_data.append([
                    f'{IO.Fore.LIGHTYELLOW_EX}{self._get_host_id(host, lock=False)}{IO.Style.RESET_ALL}',
                    host.ip or '-',
                    host.mac,
                    ipv6_display,
                    host.name,
                    host.pretty_status(),
                    bypass_str
                ])

        table = SingleTable(table_data, 'Hosts')

        if not args.force and not table.ok:
            IO.error('table does not fit terminal. resize or decrease font size. you can also force the display (--force).')
            return

        IO.spacer()
        IO.print(table.table)
        IO.spacer()

    def _limit_handler(self, args) -> None:
        hosts = self._get_hosts_by_ids(args.id)
        if hosts is None or len(hosts) == 0:
            return

        try:
            rate = BitRate.from_rate_string(args.rate)
        except Exception:
            IO.error('limit rate is invalid.')
            return

        direction = self._parse_direction_args(args)

        for host in hosts:
            self.arp_spoofer.add(host)
            if self.ndp_spoofer and host.ipv6:
                self.ndp_spoofer.add(host)
            self.limiter.limit(host, direction, rate)
            self.bandwidth_monitor.add(host)

            IO.ok(f'{IO.Fore.LIGHTYELLOW_EX}{host.ip}{IO.Style.RESET_ALL} {Direction.pretty_direction(direction)} {IO.Fore.LIGHTRED_EX}limited{IO.Style.RESET_ALL} to {rate}.')
        self._save_limits()

    def _block_handler(self, args) -> None:
        hosts = self._get_hosts_by_ids(args.id)
        direction = self._parse_direction_args(args)

        if hosts is not None and len(hosts) > 0:
            for host in hosts:
                if not host.spoofed:
                    self.arp_spoofer.add(host)
                    if self.ndp_spoofer and host.ipv6:
                        self.ndp_spoofer.add(host)

                self.limiter.block(host, direction)
                self.bandwidth_monitor.add(host)
                IO.ok(f'{IO.Fore.LIGHTYELLOW_EX}{host.ip}{IO.Style.RESET_ALL} {Direction.pretty_direction(direction)} {IO.Fore.RED}blocked{IO.Style.RESET_ALL}.')
        self._save_limits()

    def _flap_handler(self, args) -> None:
        hosts = self._get_hosts_by_ids(args.id)
        if hosts is None or len(hosts) == 0:
            return

        block_time = int(args.block_time) if args.block_time else 2
        free_time = int(args.free_time) if args.free_time else 2

        if block_time < 1 or free_time < 1:
            IO.error('durations must be at least 1 second.')
            return

        for host in hosts:
            if not host.spoofed:
                self.arp_spoofer.add(host)
                if self.ndp_spoofer and host.ipv6:
                    self.ndp_spoofer.add(host)
            self.flapper.start(host, block_time, free_time)
            self.bandwidth_monitor.add(host)
            IO.ok(f'{IO.Fore.LIGHTYELLOW_EX}{host.ip}{IO.Style.RESET_ALL} flapping ({block_time}s block / {free_time}s free).')

    def _free_handler(self, args) -> None:
        hosts = self._get_hosts_by_ids(args.id)
        if hosts is not None and len(hosts) > 0:
            for host in hosts:
                self._free_host(host)
                if self.ndp_spoofer:
                    self.ndp_spoofer.remove(host)
        self._save_limits()

    def _block_all_handler(self, args) -> None:
        with self.hosts_lock:
            hosts = list(self.hosts)
        for host in hosts:
            if not host.spoofed:
                self.arp_spoofer.add(host)
                if self.ndp_spoofer and host.ipv6:
                    self.ndp_spoofer.add(host)
            self.limiter.block(host, Direction.BOTH)
            self.bandwidth_monitor.add(host)
        self._save_limits()
        IO.ok(f'{len(hosts)} host(s) blocked.')

    def _unblock_all_handler(self, args) -> None:
        with self.hosts_lock:
            hosts = list(self.hosts)
        for host in hosts:
            self._free_host(host)
        self._save_limits()
        IO.ok(f'{len(hosts)} host(s) freed.')

    def _history_handler(self, args) -> None:
        pm = IO.get_prompt_manager()
        if pm is None or not pm.history_store:
            IO.error('no command history.')
            return
        IO.print(f'{IO.Style.BRIGHT}Command History:{IO.Style.RESET_ALL}')
        for i, cmd in enumerate(pm.history_store, 1):
            IO.print(f'  {IO.Fore.LIGHTYELLOW_EX}{i:>3}{IO.Style.RESET_ALL}  {cmd}')

    def _refresh_handler(self, args) -> None:
        with self.hosts_lock:
            old_hosts = list(self.hosts)
        for host in old_hosts:
            new_mac = netutils.get_mac_by_ip(self.interface, host.ip)
            if new_mac and new_mac != host.mac:
                IO.ok(f'{host.ip} MAC changed: {host.mac} → {new_mac}')
                host.mac = new_mac
        IO.ok('host list refreshed.')

    def _sort_handler(self, args) -> None:
        field = args.field.lower()
        reverse = False
        if field.startswith('r'):
            reverse = True
            field = field[1:]

        with self.hosts_lock:
            if field == 'ip':
                self.hosts.sort(key=lambda h: [int(o) for o in h.ip.split('.')] if h.ip else [0], reverse=reverse)
            elif field == 'name':
                self.hosts.sort(key=lambda h: h.name or '', reverse=reverse)
            elif field == 'mac':
                self.hosts.sort(key=lambda h: h.mac, reverse=reverse)
            elif field == 'id':
                pass
            elif field == 'status':
                self.hosts.sort(key=lambda h: (not h.blocked, not h.limited, not h.spoofed), reverse=reverse)
            else:
                IO.error(f'unknown field: {field}. try: ip, name, mac, id, status')
                return
        IO.ok(f'sorted by {field}.')

    def _select_handler(self, args) -> None:
        hosts = self._get_hosts_by_ids(args.id)
        if hosts is None or len(hosts) == 0:
            return
        host = next(iter(hosts))
        self._selected_host = host
        idx = self._get_host_id(host)
        self.prompt = f'{IO.Style.BRIGHT}Main{IO.Style.RESET_ALL} [{idx}:{host.ip}] >>> '
        IO.ok(f'selected {host.ip}.')

    def _selected_handler(self, args) -> None:
        if self._selected_host is None:
            IO.error('no host selected. use select [ID].')
            return
        idx = self._get_host_id(self._selected_host)
        IO.print(f'selected: [{idx}] {self._selected_host.ip} ({self._selected_host.mac})')

    def _back_handler(self, args) -> None:
        self._selected_host = None
        self.prompt = f'{IO.Style.BRIGHT}Main{IO.Style.RESET_ALL} >>> '
        IO.ok('deselected.')

    def _add_handler(self, args) -> None:
        ip = args.ip
        is_ipv6 = netutils.validate_ipv6_address(ip)

        if not is_ipv6 and not netutils.validate_ip_address(ip):
            IO.error('invalid ip address.')
            return

        if args.mac:
            mac = args.mac
            if not netutils.validate_mac_address(mac):
                IO.error('invalid mac address.')
                return
        else:
            if is_ipv6:
                mac = netutils.get_mac_by_ipv6(self.interface, ip)
            else:
                mac = netutils.get_mac_by_ip(self.interface, ip)
            if mac is None:
                IO.error('unable to resolve mac address. specify manually (--mac).')
                return

        name = None
        try:
            host_info = socket.gethostbyaddr(ip)
            name = None if host_info is None else host_info[0]
        except socket.herror:
            pass

        if is_ipv6:
            host = Host('', mac, name, ipv6=[ip])
        else:
            host = Host(ip, mac, name)

        with self.hosts_lock:
            if host in self.hosts:
                IO.error('host does already exist.')
                return

            self.hosts.append(host) 

        IO.ok('host added.')

    def _get_bandwidth_results(self) -> list[tuple]:
        with self.hosts_lock:
            results = [(h, self.bandwidth_monitor.get(h)) for h in self.hosts]
            return [(h, r) for h, r in results if r is not None]

    def _monitor_display(self, stdscr, interval: float) -> None:
        host_results = self._get_bandwidth_results()
        hname_max_len = max(len(x[0].name) for x in host_results)

        header_off = [
            ('ID', 5), ('IP address', 18), ('Hostname', hname_max_len + 2),
            ('Current (per s)', 20), ('Total', 16), ('Packets', 0)
        ]

        y_rst, x_rst = 1, 2

        while True:
            y_off, x_off = y_rst, x_rst
            stdscr.clear()

            for header in header_off:
                stdscr.addstr(y_off, x_off, header[0])
                x_off += header[1]

            y_off += 2
            x_off = x_rst

            for host, result in host_results:
                result_data = [
                    str(self._get_host_id(host)),
                    host.ip,
                    host.name,
                    f'{result.upload_rate}↑ {result.download_rate}↓',
                    f'{result.upload_total_size}↑ {result.download_total_size}↓',
                    f'{result.upload_total_count}↑ {result.download_total_count}↓'
                ]

                for j, string in enumerate(result_data):
                    stdscr.addstr(y_off, x_off, string)
                    x_off += header_off[j][1]

                y_off += 1
                x_off = x_rst

            y_off += 2
            stdscr.addstr(y_off, x_off, "press 'ctrl+c' to exit.")

            try:
                stdscr.refresh()
                time.sleep(interval)
                host_results = self._get_bandwidth_results()
            except KeyboardInterrupt:
                return

    def _monitor_handler(self, args) -> None:
        interval = 0.5
        if args.interval:
            if not args.interval.isdigit():
                IO.error('invalid interval.')
                return
            interval = int(args.interval) / 1000

        hosts_to_monitor = []
        if args.id:
            hosts = self._get_hosts_by_ids(args.id)
            if hosts is None or len(hosts) == 0:
                return
            hosts_to_monitor = list(hosts)
        elif self.hosts:
            hosts_to_monitor = list(self.hosts)
        else:
            IO.error('no hosts to be monitored. scan the network first.')
            return

        for host in hosts_to_monitor:
            if not host.spoofed:
                self.arp_spoofer.add(host)
                if self.ndp_spoofer and host.ipv6:
                    self.ndp_spoofer.add(host)
            self.bandwidth_monitor.add(host)

        time.sleep(1)
        try:
            curses.wrapper(self._monitor_display, interval)
        except curses.error:
            IO.error('monitor error occurred. maybe terminal too small?')

    def _graph_handler(self, args) -> None:
        interval = 1.0
        if args.interval:
            interval = max(0.5, int(args.interval) / 1000)
        duration = 0
        if args.duration:
            duration = max(1, int(args.duration))

        host_results = self._get_bandwidth_results()
        use_promiscuous = False

        if not host_results:
            if not self.hosts:
                IO.error('no hosts discovered. scan the network first (scan).')
                return
            use_promiscuous = True
            IO.ok(f'sniffing all traffic for {duration if duration else "unlimited"}s...')
            self.bandwidth_monitor.start_promiscuous(duration=0)

        graph = LiveGraph()
        start = time.time()
        try:
            while True:
                IO.clear()
                IO.print(get_main_banner(self.version))

                if use_promiscuous:
                    summary = self.bandwidth_monitor.get_promiscuous_summary(top_n=20)
                    IO.print(f'{IO.Style.BRIGHT}Top Talkers (promiscuous mode){IO.Style.RESET_ALL}')
                    for ip, total_bytes, direction in summary[:10]:
                        rate_bps = total_bytes * 8 / max(interval, 0.1)
                        label = f'{direction:<8}'
                        bar = '█' * min(30, max(1, int(rate_bps / 10000))) if rate_bps > 0 else '░'
                        IO.print(f'  {ip:<20} {label} {bar} {LiveGraph.format_rate(int(rate_bps))}')
                else:
                    host_results = self._get_bandwidth_results()
                    if not host_results:
                        break
                    for host, result in host_results:
                        hid = str(self._get_host_id(host))
                        graph.add_sample(hid, result.upload_rate.rate, result.download_rate.rate)
                    IO.print(graph.render())

                IO.print(f"\nInterval: {interval}s | Ctrl+C to stop")
                if duration and (time.time() - start) >= duration:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            pass

    def _analyze_handler(self, args) -> None:
        hosts = self._get_hosts_by_ids(args.id)
        if not hosts:
            IO.error('no hosts to be analyzed.')
            return

        duration = 30
        if args.duration:
            if not args.duration.isdigit():
                IO.error('invalid duration.')
                return
            duration = int(args.duration)

        hosts_to_be_freed: set[Host] = set()
        prev_samples: dict[Host, tuple] = {}

        for host in hosts:
            if not host.spoofed:
                hosts_to_be_freed.add(host)

            self.arp_spoofer.add(host)
            self.bandwidth_monitor.add(host)

            result = self.bandwidth_monitor.get(host)
            prev_samples[host] = (result.upload_total_size, result.download_total_size)

        IO.ok(f'analyzing traffic for {duration}s.')
        time.sleep(duration)

        error_occurred = False
        current_samples: dict[Host, tuple] = {}

        for host in hosts:
            result = self.bandwidth_monitor.get(host)
            if result is None:
                IO.error('host reconnected during analysis.')
                error_occurred = True
            else:
                current_samples[host] = (result.upload_total_size, result.download_total_size)

        IO.ok('cleaning up...')
        for host in hosts_to_be_freed:
            self._free_host(host)

        if error_occurred:
            return

        upload_chart = BarChart(max_bar_length=29)
        download_chart = BarChart(max_bar_length=29)

        for host in hosts:
            prev_up, prev_down = prev_samples[host]
            curr_up, curr_down = current_samples[host]
            upload_value = curr_up - prev_up
            download_value = curr_down - prev_down

            prefix = f'{IO.Fore.LIGHTYELLOW_EX}{self._get_host_id(host)}{IO.Style.RESET_ALL} ({host.ip}, {host.name})'

            upload_chart.add_value(upload_value.value, prefix, upload_value)
            download_chart.add_value(download_value.value, prefix, download_value)

        upload_table = SingleTable([[upload_chart.get()]], 'Upload')
        download_table = SingleTable([[download_chart.get()]], 'Download')

        upload_table.inner_heading_row_border = False
        download_table.inner_heading_row_border = False

        IO.spacer()
        IO.print(upload_table.table)
        IO.print(download_table.table)
        IO.spacer()

    def _watch_handler(self, args) -> None:
        if len(args) == 0:
            watch_table_data: list[list[str]] = [[
                f'{IO.Style.BRIGHT}ID{IO.Style.RESET_ALL}',
                f'{IO.Style.BRIGHT}IP address{IO.Style.RESET_ALL}',
                f'{IO.Style.BRIGHT}MAC address{IO.Style.RESET_ALL}'
            ]]

            set_table_data: list[list[str]] = [[
                f'{IO.Style.BRIGHT}Attribute{IO.Style.RESET_ALL}',
                f'{IO.Style.BRIGHT}Value{IO.Style.RESET_ALL}'
            ]]

            hist_table_data: list[list[str]] = [[
                f'{IO.Style.BRIGHT}ID{IO.Style.RESET_ALL}',
                f'{IO.Style.BRIGHT}Old IP address{IO.Style.RESET_ALL}',
                f'{IO.Style.BRIGHT}New IP address{IO.Style.RESET_ALL}',
                f'{IO.Style.BRIGHT}Time{IO.Style.RESET_ALL}'
            ]]

            iprange = self.host_watcher.iprange
            interval = self.host_watcher.interval

            set_table_data.append([
                f'{IO.Fore.LIGHTYELLOW_EX}range{IO.Style.RESET_ALL}',
                f'{len(iprange)} addresses' if iprange is not None else 'default'
            ])

            set_table_data.append([
                f'{IO.Fore.LIGHTYELLOW_EX}interval{IO.Style.RESET_ALL}',
                f'{interval}s'
            ])

            for host in self.host_watcher.hosts:
                watch_table_data.append([
                    f'{IO.Fore.LIGHTYELLOW_EX}{self._get_host_id(host)}{IO.Style.RESET_ALL}',
                    host.ip,
                    host.mac
                ])

            for recon in self.host_watcher.log_list:
                hist_table_data.append([
                    recon['old'].mac,
                    recon['old'].ip,
                    recon['new'].ip,
                    recon['time']
                ])

            watch_table = SingleTable(watch_table_data, "Watchlist")
            set_table = SingleTable(set_table_data, "Settings")
            hist_table = SingleTable(hist_table_data, 'Reconnection History')

            IO.spacer()
            IO.print(watch_table.table)
            IO.spacer()
            IO.print(set_table.table)
            IO.spacer()
            IO.print(hist_table.table)
            IO.spacer()

    def _watch_add_handler(self, args) -> None:
        hosts = self._get_hosts_by_ids(args.id)
        if hosts is None or len(hosts) == 0:
            return

        for host in hosts:
            self.host_watcher.add(host)

    def _watch_remove_handler(self, args) -> None:
        hosts = self._get_hosts_by_ids(args.id)
        if hosts is None or len(hosts) == 0:
            return

        for host in hosts:
            self.host_watcher.remove(host)

    def _watch_set_handler(self, args) -> None:
        if args.attribute.lower() in ('range', 'iprange', 'ip_range'):
            iprange = self._parse_iprange(args.value)
            if iprange is not None:
                self.host_watcher.iprange = iprange
            else:
                IO.error('invalid ip range.')
        elif args.attribute.lower() in ('interval'):
            if args.value.isdigit():
                self.host_watcher.interval = int(args.value)
            else:
                IO.error('invalid interval.')
        else:
            IO.error(f'{IO.Fore.LIGHTYELLOW_EX}{args.attribute}{IO.Style.RESET_ALL} is an invalid settings attribute.')

    def _reconnect_callback(self, old_host: Host, new_host: Host) -> None:
        with self.hosts_lock:
            if old_host in self.hosts:
                self.hosts[self.hosts.index(old_host)] = new_host
            else:
                return

        self.arp_spoofer.remove(old_host, restore=False)
        self.arp_spoofer.add(new_host)

        self.host_watcher.remove(old_host)
        self.host_watcher.add(new_host)

        self.limiter.replace(old_host, new_host)
        self.bandwidth_monitor.replace(old_host, new_host)

    def _clear_handler(self, args) -> None:
        IO.clear()
        IO.print(get_main_banner(self.version))
        self._print_help_reminder()

    def _help_handler(self, args) -> None:
        s = ' ' * 35
        y = IO.Fore.LIGHTYELLOW_EX
        r = IO.Style.RESET_ALL
        b = IO.Style.BRIGHT

        scan_len = len('scan (--range [IP range])')
        hosts_len = len('hosts (--force)')
        limit_len = len('limit [ID1,ID2,...] [rate]')
        ud_len = len('      (--upload) (--download)')
        block_len = len('block [ID1,ID2,...]')
        blockall_len = len('blockall')
        unblockall_len = len('unblockall')
        free_len = len('free [ID1,ID2,...]')
        add_len = len('add [IP] (--mac [MAC])')
        mon_len = len('monitor [ID1,ID2,...] (--interval [time in ms])')
        anal_len = len('analyze [ID1,ID2,...]')
        dur_len = len('        (--duration [time in s])')
        watch_len = len('watch')
        watch_add_len = len('watch add [ID1,ID2,...]')
        watch_rem_len = len('watch remove [ID1,ID2,...]')
        watch_set_len = len('watch set [attr] [value]')
        flap_len = len('flap [ID1,ID2,...]')
        graph_len = len('graph (--interval [ms]) (--duration [s])')
        history_len = len('history')
        refresh_len = len('refresh')
        sort_len = len('sort [ip|name|mac|id|status]')
        select_len = len('select [ID]')
        clear_len = len('clear')
        debug_len = len('debug')
        quit_len = len('quit')

        IO.print(
            f"""
{b}--- QUICK START ---{r}
  {b}1.{r} {y}scan{r}                          → find devices on network
  {b}2.{r} {y}hosts{r}                         → see device IDs
  {b}3.{r} {y}limit [ID] [rate]{r}             → throttle bandwidth
  {b}4.{r} {y}graph{r}                         → watch live bandwidth
  {b}5.{r} {y}quit{r}                          → cleanup & exit

{b}--- COMMANDS ---{r}

{y}scan (--range [IP range]){r}{s[scan_len:]}scans for online hosts on your network.
{s}required to find the hosts you want to limit.
{b}{s}e.g.: scan
{s}      scan --range 192.168.178.1-192.168.178.50
{s}      scan --range 192.168.178.1/24{r}

{y}hosts (--force){r}{s[hosts_len:]}lists all scanned hosts.
{s}shows ID, IP, MAC, IPv6, hostname, status, and bypass detection.
{s}the Bypass column shows {y}BYPASS{r} (spoof overridden) or {y}WARN{r} (ARP mismatch).

{y}limit [ID1,ID2,...] [rate]{r}{s[limit_len:]}limits bandwith of host(s) (upload+download).
{y}      (--upload) (--download){r}{s[ud_len:]}{b}e.g.: limit 4 100kbit
{s}      limit 2,3,4 1gbit --download
{s}      limit all 200kbit --upload{r}
{s}supported rate formats: 500kbit, 1mbit, 10mbit, 1gbit

{y}block [ID1,ID2,...]{r}{s[block_len:]}blocks internet access of host(s).
{y}      (--upload) (--download){r}{s[ud_len:]}{b}e.g.: block 3,2
{s}      block all --upload{r}

{y}blockall{r}{s[blockall_len:]}blocks internet for ALL discovered hosts at once.
{s}no arguments needed. use {y}unblockall{r} to revert.

{y}unblockall{r}{s[unblockall_len:]}frees ALL hosts at once (unlimits + unblocks).

{y}free [ID1,ID2,...]{r}{s[free_len:]}unlimits/unblocks host(s).
{b}{s}e.g.: free 3
{s}      free all{r}

{y}flap [ID1,ID2,...]{r}{s[flap_len:]}blokir-bebasin host bergantian terus.
{y}      (--block [sec]) (--free [sec]){r}{s[ud_len:]}{b}e.g.: flap 6
{s}      flap 6 --block 3 --free 1
{s}      flap all --block 5 --free 2{r}

{y}graph (--interval [ms]) (--duration [s]){r}{s[graph_len:]}live bandwidth graph.
{s}shows real-time upload/download per host.
{s}if no hosts are limited, automatically sniffs ALL traffic (promiscuous).{b}
{s}e.g.: graph --interval 1000 --duration 30
{s}      graph  (shows up to 20 top talkers){r}

{y}add [IP] (--mac [MAC]){r}{s[add_len:]}adds custom host to host list.
{s}mac resolved automatically.
{b}{s}e.g.: add 192.168.178.24
{s}      add 192.168.1.50 --mac 1c:fc:bc:2d:a6:37{r}

{y}monitor [ID1,ID2,...] (--interval [time in ms]){r}{s[mon_len:]}monitors bandwidth usage of host(s) in real-time.
{s}if no IDs given, monitors ALL hosts automatically.
{s}curses-based real-time display (Ctrl+C to exit).{b}
{s}e.g.: monitor
{s}      monitor 2,3
{s}      monitor all --interval 600{r}

{y}analyze [ID1,ID2,...]{r}{s[anal_len:]}analyzes traffic of host(s) without limiting
{y}        (--duration [time in s]){r}{s[dur_len:]}to determine who uses how much bandwidth.
{s}shows bar charts for upload and download.{b}
{s}e.g.: analyze 2,3 --duration 120{r}

{y}watch{r}{s[watch_len:]}detects host reconnects with different IP.
{y}watch add [ID1,ID2,...]{r}{s[watch_add_len:]}adds host to the reconnection watchlist.
{s}when a host reconnects with a new IP, limits are auto-reapplied.{b}
{s}e.g.: watch add 3,4{r}
{y}watch remove [ID1,ID2,...]{r}{s[watch_rem_len:]}removes host from the reconnection watchlist.
{b}{s}e.g.: watch remove all{r}
{y}watch set [attr] [value]{r}{s[watch_set_len:]}changes reconnect watch settings.
{b}{s}e.g.: watch set interval 120{r}

{y}history{r}{s[history_len:]}shows recently used commands.
{b}{s}e.g.: history{r}

{y}refresh{r}{s[refresh_len:]}re-resolves MAC addresses for all hosts.
{s}useful after ARP table changes.

{y}sort [field]{r}{s[sort_len:]}sorts host list by ip/name/mac/id/status.
{b}{s}e.g.: sort ip
{s}      sort rname (reverse sort){r}

{y}select [ID]{r}{s[select_len:]}selects a host and updates the prompt.
{s}use 'back' or 'selected' to manage selection.

{y}selected{r}{s[select_len:]}shows the currently selected host.

{y}back{r}{s[select_len:]}deselects the current host and restores prompt.

{y}clear{r}{s[clear_len:]}clears the terminal window.

{y}debug{r}{s[debug_len:]}shows diagnostic info (iptables, ip_forward, spoof state).

{y}quit{r}{s[quit_len:]}quits the application (cleans up spoof, limits, monitor).
            """
        )

    def _debug_handler(self, args) -> None:
        import subprocess
        IO.spacer()
        IO.print(f'{IO.Style.BRIGHT}=== Diagnostics ==={IO.Style.RESET_ALL}')

        with open('/proc/sys/net/ipv4/ip_forward') as f:
            ipf = f.read().strip()
        IO.print(f'IP Forward: {IO.Fore.LIGHTYELLOW_EX}{ipf}{IO.Style.RESET_ALL}')

        try:
            r = subprocess.run(['iptables', '-t', 'filter', '-L', 'FORWARD', '-n', '-v'],
                             capture_output=True, text=True, timeout=3)
            IO.print(f'{IO.Style.BRIGHT}FORWARD chain:{IO.Style.RESET_ALL}')
            for line in r.stdout.split('\n'):
                IO.print(f'  {line}')
        except Exception as e:
            IO.print(f'  iptables error: {e}')

        IO.print(f'{IO.Style.BRIGHT}Spoofed hosts:{IO.Style.RESET_ALL}')
        with self.hosts_lock:
            for host in self.hosts:
                if host.spoofed:
                    IO.print(f'  {host.ip} ({host.mac}) - limited={host.limited} blocked={host.blocked}')

        IO.spacer()

    def _quit_handler(self, args) -> None:
        self.interrupt_handler(False)
        self.stop()

    def _save_limits(self) -> None:
        if not self.config.get('autosave_limits', True):
            return
        with self.limiter._host_dict_lock:
            host_dict = dict(self.limiter._host_dict)
        persist_module.save_limits(host_dict)

    def _get_host_id(self, host: Host, lock: bool = True) -> int | None:
        ret = None

        if lock:
            self.hosts_lock.acquire()

        for i, host_ in enumerate(self.hosts):
            if host_ == host:
                ret = i
                break
        
        if lock:
            self.hosts_lock.release()

        return ret

    def _print_help_reminder(self) -> None:
        IO.print(f'type {IO.Fore.LIGHTYELLOW_EX}help{IO.Style.RESET_ALL} or {IO.Fore.LIGHTYELLOW_EX}?{IO.Style.RESET_ALL} to show command information.')

    def _get_hosts_by_ids(self, ids_string: str) -> set | None:
        if ids_string == 'all':
            with self.hosts_lock:
                return set(self.hosts)

        ids = ids_string.split(',')
        hosts: set[Host] = set()

        with self.hosts_lock:
            for id_ in ids:
                host = self._find_host(id_)
                if host is None:
                    return None
                hosts.add(host)

        return hosts

    def _find_host(self, id_: str) -> Host | None:
        if netutils.validate_mac_address(id_):
            for host in self.hosts:
                if host.mac == id_.lower():
                    return host
            IO.error(f'no host matching {id_}.')
            return None

        if netutils.validate_ip_address(id_):
            for host in self.hosts:
                if host.ip == id_:
                    return host
            IO.error(f'no host matching {id_}.')
            return None

        if id_.isdigit():
            idx = int(id_)
            if 0 <= idx < len(self.hosts):
                return self.hosts[idx]
            IO.error(f'no host with id {id_}.')
            return None

        IO.error(f'invalid identifier(s): \'{id_}\'.')
        return None

    def _parse_direction_args(self, args) -> Direction:
        direction = Direction.NONE

        if args.upload:
            direction |= Direction.OUTGOING
        if args.download:
            direction |= Direction.INCOMING

        return Direction.BOTH if direction == Direction.NONE else direction

    def _parse_iprange(self, iprange_str: str) -> list | None:
        try:
            if '-' in iprange_str:
                return list(netaddr.iter_iprange(*iprange_str.split('-')))
            else:
                return list(netaddr.IPNetwork(iprange_str))
        except netaddr.core.AddrFormatError:
            return

    def _free_host(self, host: Host) -> None:
        self.flapper.stop(host)
        if host.spoofed:
            self.arp_spoofer.remove(host)
            if self.ndp_spoofer:
                self.ndp_spoofer.remove(host)
        self.limiter.unlimit(host, Direction.BOTH)
        self.bandwidth_monitor.remove(host)
        self.host_watcher.remove(host)
