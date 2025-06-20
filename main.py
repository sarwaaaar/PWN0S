import sys
sys.dont_write_bytecode = True
import subprocess
from loading import clear_screen, loading_state
import readline
import os
import difflib
import shutil
import time
import zipfile
import io
from INTERFACEPLUGS.blackout.blackout import BlackoutESP32

VERSION = "0.0.8"

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[38;2;204;103;102m"
PINK = "\033[38;2;227;148;220m"
YELLOW = "\033[93m"
GREEN = "\033[38;2;180;189;104m"

# Command mapping: full command to short form
COMMAND_ALIASES = {
    "quickhack": "qh",
    "daemon": "d",
    "interfaceplug": "ifp",
    "exit": "q",
    "quit": "q",
}
# Inverse mapping: short form to full command
SHORT_TO_FULL = {v: k for k, v in COMMAND_ALIASES.items()}
# All valid commands (full and short forms)
COMMANDS = list(COMMAND_ALIASES.keys()) + list(SHORT_TO_FULL.keys())

# Define PROJECT_ROOT for robust path handling
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Read ASCII art from shared file
ASCII_ART_PATH = os.path.join(PROJECT_ROOT, 'ascii.txt')
try:
    with open(ASCII_ART_PATH, 'r', encoding='utf-8') as f:
        ASCII_ART = f.read()
except Exception:
    ASCII_ART = ''

def print_ascii_art():
    if ASCII_ART:
        print()  # Blank line above
        print(ASCII_ART)
        print()  # Blank line below

def completer(text, state):
    options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    if state < len(options):
        return options[state] + ' '
    return None

readline.set_completer(completer)
readline.parse_and_bind('tab: complete')

HISTFILE = '.pwn0s_history'
try:
    readline.read_history_file(HISTFILE)
except FileNotFoundError:
    pass
import atexit
def save_history():
    readline.write_history_file(HISTFILE)
atexit.register(save_history)

def print_command_guide():
    print(f"{BOLD}{PINK}Available Commands:{RESET}")
    print(f"  {PINK}quickhack{RESET} (qh)     - {YELLOW}Network tools and utilities{RESET}")
    print(f"  {PINK}daemon{RESET} (d)         - {YELLOW}Background services and automation{RESET}")
    print(f"  {PINK}interfaceplug{RESET} (ifp) - {YELLOW}Hardware and interface tools{RESET}")
    print(f"  {PINK}exit{RESET} (q)           - {YELLOW}Exit PWN0S{RESET}")
    print()

def print_quickhack_guide():
    print(f"{BOLD}{PINK}quickhack Command Options:{RESET}")
    print(f"  {PINK}shortcirc{RESET} (sc)     - {YELLOW}Denial-of-service toolkit{RESET}")
    print(f"  {PINK}ping{RESET} (pg)          - {YELLOW}Information gathering and tracking{RESET}")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  quickhack shortcirc -target 192.168.1.1:80 -method UDP -time 60")
    print(f"  quickhack ping -ip 8.8.8.8")
    print(f"  quickhack ping -seeker -t 1 -p 8080")

def print_shortcirc_guide():
    print(f"{BOLD}{PINK}shortcirc - Denial-of-Service Toolkit{RESET}")
    print(f"{YELLOW}Description:{RESET} Advanced DDoS toolkit with multiple attack vectors")
    print()
    print(f"{BOLD}{PINK}Options:{RESET}")
    print(f"  -target <ip:port/url/phone>  Target specification")
    print(f"  -method <attack_type>        Attack method (SMS/EMAIL/NTP/UDP/SYN/ICMP/POD/MEMCACHED/HTTP/SLOWLORIS)")
    print(f"  -time <seconds>              Attack duration")
    print(f"  -threads <count>             Number of threads (1-200)")
    print(f"  -h                           Show this help")
    print()
    print(f"{YELLOW}Attack Methods:{RESET}")
    print(f"  SMS/EMAIL     - SMS/Email bombing")
    print(f"  NTP/UDP/SYN   - Network flooding")
    print(f"  ICMP/POD      - Ping of Death")
    print(f"  MEMCACHED     - Memcached amplification")
    print(f"  HTTP/SLOWLORIS- HTTP-based attacks")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  shortcirc -target 192.168.1.1:80 -method UDP -time 60 -threads 10")
    print(f"  shortcirc -target example.com -method HTTP -time 120 -threads 50")

def print_ping_guide():
    print(f"{BOLD}{PINK}ping - Information Gathering Toolkit{RESET}")
    print(f"{YELLOW}Description:{RESET} Comprehensive OSINT and tracking tools")
    print()
    print(f"{BOLD}{PINK}Options:{RESET}")
    print(f"  -ip <address>                IP address tracker")
    print(f"  -sip                         Show your IP address")
    print(f"  -pn <number>                 Phone number tracker")
    print(f"  -ut <username>               Username tracker")
    print(f"  -seeker                      Launch seeker phishing toolkit")
    print(f"  -h                           Show this help")
    print(f"  -q                           Exit")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  ping -ip 8.8.8.8")
    print(f"  ping -pn +1234567890")
    print(f"  ping -ut username")
    print(f"  ping -seeker -t 1 -p 8080")

def print_seeker_guide():
    print(f"{BOLD}{PINK}seeker - Phishing Toolkit{RESET}")
    print(f"{YELLOW}Description:{RESET} Advanced phishing framework with location tracking")
    print()
    print(f"{BOLD}{PINK}Options:{RESET}")
    print(f"  -t, --template <num>         Template number (required)")
    print(f"  -k, --kml <filename>         KML filename")
    print(f"  -p, --port <port>            Web server port (default: 8080)")
    print(f"  -u, --update                 Check for updates")
    print(f"  -v, --version                Show version")
    print(f"  -d, --debugHTTP <bool>       Disable HTTPS redirection")
    print(f"  -tg, --telegram <token:chatId> Telegram bot API token")
    print(f"  -wh, --webhook <url>         Webhook URL")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  seeker -t 1 -p 8080")
    print(f"  seeker -t 2 -k output.kml")

def print_daemon_guide():
    print(f"{BOLD}{PINK}daemon Command Options:{RESET}")
    print(f"  {PINK}rabids{RESET}           - {YELLOW}Automated payload builder{RESET}")
    print(f"  {PINK}filedaemon{RESET}       - {YELLOW}HTTP file server{RESET}")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  daemon -rabids -lhost 192.168.1.100 -lport 4444 -key 123 -output payload")
    print(f"  daemon -filedaemon -start")

def print_rabids_guide():
    print(f"{BOLD}{PINK}rabids - Automated Payload Builder{RESET}")
    print(f"{YELLOW}Description:{RESET} Rust-based payload generator with XOR encryption")
    print()
    print(f"{BOLD}{PINK}Options:{RESET}")
    print(f"  -lhost <ip>                  Listener IP address")
    print(f"  -lport <port>                Listener port")
    print(f"  -key <number>                XOR encryption key")
    print(f"  -output <filename>           Output file name")
    print(f"  -platform <os>               Target platform (windows/linux/mac)")
    print(f"  -h                           Show this help")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  rabids -lhost 192.168.1.100 -lport 4444 -key 123 -output payload")
    print(f"  rabids -lhost 10.0.0.1 -lport 8080 -key 456 -output backdoor -platform windows")

def print_filedaemon_guide():
    print(f"{BOLD}{PINK}filedaemon - HTTP File Server{RESET}")
    print(f"{YELLOW}Description:{RESET} Simple HTTP server for file sharing and payload delivery")
    print()
    print(f"{BOLD}{PINK}Options:{RESET}")
    print(f"  -start, -s                   Start HTTP server")
    print(f"  -clean, -c                   Clean 'dir' folder contents")
    print(f"  -h                           Show this help")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  filedaemon -start")
    print(f"  filedaemon -clean")

def print_interfaceplug_guide():
    print(f"{BOLD}{PINK}interfaceplug Command Options:{RESET}")
    print(f"  {PINK}blackout{RESET} (b)     - {YELLOW}ESP32 hardware interface{RESET}")
    print(f"  {PINK}deck{RESET}             - {YELLOW}SSH connection manager{RESET}")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  interfaceplug -blackout -scan")
    print(f"  interfaceplug -blackout -connect 192.168.1.100")
    print(f"  interfaceplug -deck")

def print_blackout_guide():
    print(f"{BOLD}{PINK}blackout - ESP32 Hardware Interface{RESET}")
    print(f"{YELLOW}Description:{RESET} ESP32 microcontroller communication and control")
    print()
    print(f"{BOLD}{PINK}Options:{RESET}")
    print(f"  -connect <server_ip>         Connect to ESP32 server")
    print(f"  -scan                        Scan available serial ports")
    print(f"  -connect -p <device>         Connect to specific ESP32 device")
    print(f"  -send <command>              Send command to ESP32")
    print(f"  -h                           Show this help")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  blackout -scan")
    print(f"  blackout -connect 192.168.1.100")
    print(f"  blackout -connect -p /dev/ttyUSB0")
    print(f"  blackout -send 'LED_ON'")

def print_deck_guide():
    print(f"{BOLD}{PINK}deck - SSH Connection Manager{RESET}")
    print(f"{YELLOW}Description:{RESET} Automated SSH connection using stored credentials")
    print()
    print(f"{BOLD}{PINK}Options:{RESET}")
    print(f"  -username <user>             SSH username")
    print(f"  -ip <address>                Target IP address")
    print(f"  -password <pass>             SSH password")
    print(f"  -h                           Show this help")
    print()
    print(f"{YELLOW}Usage Examples:{RESET}")
    print(f"  deck                                    # Use existing config.json")
    print(f"  deck -username admin -ip 192.168.1.100 -password mypass123")
    print()
    print(f"{YELLOW}Configuration:{RESET}")
    print(f"  Config file: INTERFACEPLUGS/deck/config.json")
    print(f"  Format: {{\"username\": \"user\", \"ip\": \"ip\", \"password\": \"pass\"}}")

def suggest_command(user_cmd, valid_cmds):
    matches = difflib.get_close_matches(user_cmd, valid_cmds, n=2, cutoff=0.6)
    if matches:
        print(f"{YELLOW}Did you mean: {', '.join(matches)}{RESET}")

def suggest_subcommand_option(user_opt, valid_opts):
    matches = difflib.get_close_matches(user_opt, valid_opts, n=2, cutoff=0.6)
    if matches:
        print(f"{YELLOW}Did you mean: {', '.join(matches)}{RESET}")

def run_command(cmdline):
    parts = cmdline.strip().split()
    if not parts:
        return True  # Return True for empty commands
    cmd = parts[0].lower()
    BASIC_TERMINAL_COMMANDS = [
        'ls', 'pwd', 'cat', 'echo', 'mkdir', 'rm', 'touch', 'cp', 'mv', 'whoami', 'date', 'head', 'tail', 'grep', 'find', 'chmod', 'chown', 'rmdir', 'tree', 'df', 'du', 'which', 'uname', 'ps', 'kill', 'top'
    ]
    if cmd in BASIC_TERMINAL_COMMANDS:
        try:
            result = subprocess.run(parts, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(f"{RED}{result.stderr}{RESET}", end='')
        except Exception as e:
            print(f"{RED}[!] Failed to execute command: {e}{RESET}")
        return True
    if cmd in SHORT_TO_FULL:
        cmd = SHORT_TO_FULL[cmd]
        parts[0] = cmd
    allowed_no_dash = ["quickhack", "daemon", "interfaceplug", "exit", "quit"] + list(SHORT_TO_FULL.keys())
    if cmd not in allowed_no_dash and not cmd.startswith("-"):
        print(f"{RED}[!] Unknown command '{cmd}'{RESET}")
        suggest_command(cmd, COMMANDS)
        return False  # Return False for unknown commands
    if cmd.startswith("-"):
        cmd = cmd[1:]
        parts[0] = cmd
        if cmd in SHORT_TO_FULL:
            cmd = SHORT_TO_FULL[cmd]
            parts[0] = cmd
    # if cmd != "clear":
    #     clear_screen()
    #     print_ascii_art()
    if cmd == "quickhack":
        if len(parts) < 2:
            print(f"{RED}[!] Usage: quickhack <tool> [options]{RESET}")
            print_quickhack_guide()
            return False
        tool = parts[1].lstrip('-')
        SUBCOMMAND_ALIASES = {"shortcirc": "sc", "ping": "pg"}
        SHORT_TO_SUB = {v: k for k, v in SUBCOMMAND_ALIASES.items()}
        all_subs = list(SUBCOMMAND_ALIASES.keys()) + list(SHORT_TO_SUB.keys())
        if tool in SHORT_TO_SUB:
            tool = SHORT_TO_SUB[tool]
            parts[1] = tool
        
        # Handle help for quickhack
        if tool == "help":
            print_quickhack_guide()
            return True
        
        if tool in all_subs:
            # Handle help for subcommands
            if len(parts) > 2 and parts[2] in ["help", "-help", "-h"]:
                if tool == "shortcirc":
                    print_shortcirc_guide()
                    return True
                elif tool == "ping":
                    print_ping_guide()
                    return True
                elif tool == "seeker":
                    print_seeker_guide()
                    return True
            
            if tool == "shortcirc":
                valid_opts = ['-target', '-method', '-time', '-threads', '-h', '-help']
                for arg in parts[2:]:
                    if arg.startswith('-') and arg not in valid_opts and not arg.startswith('--'):
                        print(f"{RED}[!] Unknown option '{arg}' for shortcirc{RESET}")
                        suggest_subcommand_option(arg, valid_opts)
                        print_shortcirc_guide()
                        return False
            if tool == "ping":
                valid_opts = ['-ip', '-pn', '-ut', '-sip', '-h', '-help', '-q', '-seeker']
                is_seeker = '-seeker' in parts[2:]
                if is_seeker:
                    seeker_index = parts.index('-seeker')
                    seeker_args = parts[seeker_index+1:]
                    # Handle seeker help
                    if len(seeker_args) > 0 and seeker_args[0] in ["help", "-help", "-h"]:
                        print_seeker_guide()
                        return False
                    with loading_state(message="Installing requirements for seeker...", duration=2, print_ascii_art=print_ascii_art):
                        pass
                    requirements = ["requests", "argparse", "packaging", "psutil"]
                    print(f"{YELLOW}[*] Installing requirements...{RESET}")
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + requirements, check=True)
                    except subprocess.CalledProcessError:
                        print(f"{RED}[!] Failed to install requirements{RESET}")
                        return False
                    with loading_state(message="Invoking seeker toolkit...", duration=2, print_ascii_art=print_ascii_art):
                        pass
                    script_path = os.path.join(PROJECT_ROOT, "QUICKHACKS", "ping", "seeker.py")
                    try:
                        subprocess.run([sys.executable, script_path] + seeker_args)
                    except FileNotFoundError:
                        print(f"{RED}[!] seeker script not found{RESET}")
                    return False
                for arg in parts[2:]:
                    if arg.startswith('-') and arg not in valid_opts and not arg.startswith('--'):
                        print(f"{RED}[!] Unknown option '{arg}' for ping{RESET}")
                        suggest_subcommand_option(arg, valid_opts)
                        print_ping_guide()
                        return False
                if is_seeker and ('-h' in parts[2:] or '--help' in parts[2:]):
                    print_seeker_guide()
                    return False
            # Replace with full name for script invocation
            if tool == "shortcirc":
                with loading_state(message="Installing requirements for shortcirc...", duration=2, print_ascii_art=print_ascii_art):
                    pass
                requirements = ["requests", "scapy", "wget", "argparse", "colorama", "humanfriendly"]
                print(f"{YELLOW}[*] Installing requirements...{RESET}")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + requirements, check=True)
                except subprocess.CalledProcessError:
                    print(f"{RED}[!] Failed to install requirements{RESET}")
                    return False
                with loading_state(message="Invoking shortcirc toolkit...", duration=2, print_ascii_art=print_ascii_art):
                    pass
                script_path = os.path.join(PROJECT_ROOT, "QUICKHACKS", "shortcirc", "shortcirc.py")
                try:
                    subprocess.run([sys.executable, script_path] + parts[2:])
                except FileNotFoundError:
                    print(f"{RED}[!] shortcirc script not found{RESET}")
                return False
            if tool == "ping":
                if len(parts) > 2 and parts[2] == "-seeker":
                    with loading_state(message="Installing requirements for seeker...", duration=2, print_ascii_art=print_ascii_art):
                        pass
                    requirements = ["requests", "argparse", "packaging", "psutil"]
                    print(f"{YELLOW}[*] Installing requirements...{RESET}")
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + requirements, check=True)
                    except subprocess.CalledProcessError:
                        print(f"{RED}[!] Failed to install requirements{RESET}")
                        return False
                    with loading_state(message="Invoking seeker toolkit...", duration=2, print_ascii_art=print_ascii_art):
                        pass
                    script_path = os.path.join(PROJECT_ROOT, "QUICKHACKS", "ping", "seeker.py")
                    try:
                        subprocess.run([sys.executable, script_path] + parts[3:])
                    except FileNotFoundError:
                        print(f"{RED}[!] seeker script not found{RESET}")
                    return False
                with loading_state(message="Installing requirements for ping...", duration=2, print_ascii_art=print_ascii_art):
                    pass
                requirements = ["requests", "phonenumbers"]
                print(f"{YELLOW}[*] Installing requirements...{RESET}")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + requirements, check=True)
                except subprocess.CalledProcessError:
                    print(f"{RED}[!] Failed to install requirements{RESET}")
                    return False
                with loading_state(message="Invoking ping toolkit...", duration=2, print_ascii_art=print_ascii_art):
                    pass
                script_path = os.path.join(PROJECT_ROOT, "QUICKHACKS", "ping", "ping.py")
                try:
                    subprocess.run([sys.executable, script_path] + parts[2:])
                except FileNotFoundError:
                    print(f"{RED}[!] ping script not found{RESET}")
                return False
        # If not a known subcommand, treat as external tool
        with loading_state(message=f"Launching {tool}...", duration=2, print_ascii_art=print_ascii_art):
            pass
        try:
            subprocess.run([tool] + parts[2:])
        except FileNotFoundError:
            print(f"{RED}[!] Tool '{tool}' not found{RESET} {YELLOW}Make sure it's installed in your environment or in your PATH.{RESET}")
            return False
        return False
    elif cmd == "daemon":
        if len(parts) < 2:
            print(f"{RED}[!] Usage: daemon <service> [options]{RESET}")
            print_daemon_guide()
            return False
        service = parts[1].lstrip('-')
        
        # Handle help for daemon
        if service == "help":
            print_daemon_guide()
            return True
        
        if service == "rabids":
            # Handle help for rabids
            if len(parts) > 2 and parts[2] in ["help", "-help", "-h"]:
                print_rabids_guide()
                return True
            valid_opts = ['-lhost', '-lport', '-key', '-output', '-platform', '-h', '-help']
            for arg in parts[2:]:
                if arg.startswith('-') and arg not in valid_opts and not arg.startswith('--'):
                    print(f"{RED}[!] Unknown option '{arg}' for rabids{RESET}")
                    suggest_subcommand_option(arg, valid_opts)
                    print_rabids_guide()
                    return False
            rabdis_path = os.path.join(PROJECT_ROOT, "DAEMONS", "rabids", "rabids.py")
            args = [sys.executable, rabdis_path] + parts[2:]
            with loading_state(message="Automating payload embedding and compilation...", duration=2, print_ascii_art=print_ascii_art):
                pass
            try:
                subprocess.run(args, check=True)
            except subprocess.CalledProcessError:
                print(f"{RED}[!] rabids.py failed to run properly{RESET}")
                return False
            return True
        elif service == "filedaemon":
            # Handle help for filedaemon
            if len(parts) > 2 and parts[2] in ["help", "-help", "-h"]:
                print_filedaemon_guide()
                return True
            valid_opts = ['-start', '-s', '-clean', '-c', '-h', '-help']
            for arg in parts[2:]:
                if arg.startswith('-') and arg not in valid_opts and not arg.startswith('--'):
                    print(f"{RED}[!] Unknown option '{arg}' for filedaemon{RESET}")
                    suggest_subcommand_option(arg, valid_opts)
                    print_filedaemon_guide()
                    return False
            filedaemon_path = os.path.join(PROJECT_ROOT, "DAEMONS", "filedaemon", "filedaemon.py")
            args = [sys.executable, filedaemon_path] + parts[2:]
            with loading_state(message="Starting filedaemon server...", duration=2, print_ascii_art=print_ascii_art):
                pass
            try:
                subprocess.run(args, check=True)
            except subprocess.CalledProcessError:
                print(f"{RED}[!] filedaemon.py failed to run properly{RESET}")
                return False
            return True
        else:
            print(f"{RED}[!] Unknown daemon service '{service}'{RESET}")
            print_daemon_guide()
            return False
    elif cmd == "interfaceplug":
        if len(parts) < 2:
            print(f"{RED}[!] Usage: interfaceplug <tool> [options]{RESET}")
            print()
            print_interfaceplug_guide()
            return False
        tool = parts[1].lstrip('-')
        
        # Handle help for interfaceplug
        if tool == "help":
            print_interfaceplug_guide()
            return True
        
        if tool in ["-blackout", "-b"]:
            # Handle help for blackout
            if len(parts) > 2 and parts[2] in ["help", "-help", "-h"]:
                print_blackout_guide()
                return True
            blackout = BlackoutESP32(
                output_callback=lambda msg, t='system': print(msg),
                print_ascii_art=print_ascii_art,
                YELLOW=YELLOW,
                GREEN=GREEN,
                RED=RED,
                PINK=PINK,
                RESET=RESET
            )
            args = parts[2:]
            valid_blackout_opts = ["-connect", "-c", "-scan", "-send", "-p", "-pw", "-h", "-help"]
            if not args or (args[0] not in valid_blackout_opts and not (args[0] in ["-connect", "-c"] and len(args) > 1 and args[1] in ["-p", "-pw"])):
                print(f"{RED}[!] Unknown blackout subcommand or option: '{' '.join(args)}'{RESET}")
                suggest_subcommand_option(args[0] if args else '', valid_blackout_opts)
                print_blackout_guide()
                return False
            if args[0] in ["-connect", "-c"] and len(args) == 2:
                with loading_state(message=f"Connecting to server at {args[1]}...", duration=2, print_ascii_art=print_ascii_art):
                    blackout.connect_to_server(args[1])
                return True
            elif args[0] == "-scan":
                with loading_state(message="Scanning serial ports...", duration=2, print_ascii_art=print_ascii_art):
                    blackout.scan_serial_ports()
                return True
            elif args[0] in ["-connect", "-c"] and len(args) > 2 and args[1] in ["-p", "-pw"]:
                with loading_state(message=f"Connecting to ESP32 on {args[2]}...", duration=2, print_ascii_art=print_ascii_art):
                    blackout.connect_to_esp32(args[2])
                return True
            elif args[0] == "-send" and len(args) > 1:
                with loading_state(message=f"Sending command: {' '.join(args[1:])}...", duration=2, print_ascii_art=print_ascii_art):
                    blackout.send_esp32_command(' '.join(args[1:]))
                return True
            elif args[0] == "-h":
                print_blackout_guide()
                return False
            else:
                print(f"{RED}Usage: interfaceplug -blackout -connect <server_ip> | -scan | -connect -p <device> | -send <command>{RESET}")
            return False
        elif tool == "-deck":
            # Handle help for deck
            if len(parts) > 2 and parts[2] in ["help", "-help", "-h"]:
                print_deck_guide()
                return True
            with loading_state(message="Launching SSH connection manager...", duration=2, print_ascii_art=print_ascii_art):
                pass
            deck_path = os.path.join(PROJECT_ROOT, "INTERFACEPLUGS", "deck", "deck.py")
            try:
                subprocess.run([sys.executable, deck_path] + parts[2:])
            except FileNotFoundError:
                print(f"{RED}[!] deck script not found{RESET}")
                return False
            return True
        else:
            print(f"{RED}[!] Unknown interfaceplug tool '{tool}'{RESET}")
            print_interfaceplug_guide()
            return False
    elif cmd in ["exit", "quit", "q"]:
        clear_screen()
        print_ascii_art()
        print(f"{PINK}{BOLD}Goodbye!{RESET}")
        sys.exit(0)
        return False
    else:
        print(f"{RED}[!] Unknown command '{cmd}'{RESET}")
        suggest_command(cmd, COMMANDS)
        return False

def check_dependencies():
    import importlib
    import platform
    import subprocess
    import sys
    # Try to use tqdm for a nice progress bar, fallback to simple print
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False
    # Python dependencies
    python_packages = [
        'requests', 'scapy', 'wget', 'argparse', 'colorama', 'humanfriendly', 'phonenumbers', 'packaging', 'psutil', 'tqdm'
    ]
    missing = []
    print(f"{YELLOW}{BOLD}[*] Checking Python dependencies...{RESET}")
    iterator = tqdm(python_packages, desc="Checking", ncols=70) if use_tqdm else python_packages
    for pkg in iterator:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
        if not use_tqdm:
            print(f"  {pkg}... {'OK' if pkg not in missing else 'MISSING'}")
            time.sleep(0.1)
    # Find pip or pip3
    pip_bin = shutil.which('pip') or shutil.which('pip3')
    if missing:
        if pip_bin is None:
            print(f"{RED}{BOLD}[!] Missing system dependency:{RESET} pip (pip or pip3)")
            print(f"{YELLOW}Please install pip or pip3 manually!{RESET}")
            os_name = platform.system().lower()
            if os_name == 'darwin':
                print(f"  brew install python3")
            elif os_name == 'linux':
                print(f"  sudo apt install python3-pip")
            else:
                print(f"  Download Python from https://www.python.org/downloads/")
            print()
            sys.exit(1)
        print(f"{YELLOW}{BOLD}[*] Installing missing Python packages:{RESET} {', '.join(missing)}")
        try:
            subprocess.run([pip_bin, 'install', '--break-system-packages'] + missing, check=True)
        except Exception as e:
            print(f"{RED}{BOLD}[!] Failed to install Python packages: {e}{RESET}")
            sys.exit(1)
    # System dependencies
    system_bins = {
        'php': 'PHP',
        'rustc': 'Rust',
        'cargo': 'Cargo',
        'msfvenom': 'msfvenom (Metasploit)',
    }
    missing_bins = []
    print(f"{YELLOW}{BOLD}[*] Checking system dependencies...{RESET}")
    iterator = tqdm(system_bins.items(), desc="Checking", ncols=70) if use_tqdm else system_bins.items()
    for bin, name in iterator:
        if shutil.which(bin) is None:
            missing_bins.append((bin, name))
        if not use_tqdm:
            print(f"  {name} ({bin})... {'OK' if shutil.which(bin) else 'MISSING'}")
            time.sleep(0.1)
    if pip_bin is None:
        missing_bins.append(('pip/pip3', 'pip or pip3'))
    if missing_bins:
        print(f"{RED}{BOLD}[!] Missing system dependencies:{RESET}")
        for bin, name in missing_bins:
            print(f"  {YELLOW}{name}{RESET} ({bin})")
        print(f"\n{YELLOW}Please install the missing dependencies manually:{RESET}")
        os_name = platform.system().lower()
        for bin, name in missing_bins:
            if 'php' in bin:
                if os_name == 'darwin':
                    print(f"  brew install php")
                elif os_name == 'linux':
                    print(f"  sudo apt install php")
                else:
                    print(f"  Download PHP from https://www.php.net/downloads.php")
            elif 'rustc' in bin or 'cargo' in bin:
                print(f"  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
            elif 'msfvenom' in bin:
                print(f"  Install Metasploit from https://docs.metasploit.com/docs/using-metasploit/getting-started/nightly-installers.html")
            elif 'pip' in bin:
                if os_name == 'darwin':
                    print(f"  brew install python3")
                elif os_name == 'linux':
                    print(f"  sudo apt install python3-pip")
                else:
                    print(f"  Download Python from https://www.python.org/downloads/")
        print()
        sys.exit(1)
    print(f"{GREEN}{BOLD}[✓] All dependencies satisfied!{RESET}\n")

GITHUB_REPO_URL = "https://github.com/sarwaaaar/PWN0S"
GITHUB_ZIP_URL = "https://github.com/sarwaaaar/PWN0S/archive/refs/heads/main.zip"

LATEST_VERSION_URL = "https://raw.githubusercontent.com/sarwaaaar/PWN0S/main/main.py"

def get_latest_version():
    import requests
    try:
        resp = requests.get(LATEST_VERSION_URL, timeout=10)
        if resp.status_code == 200:
            import re
            match = re.search(r'VERSION\s*=\s*["\\\']([\d.]+)["\\\']', resp.text)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"{YELLOW}[!] Could not check for updates: {e}{RESET}")
    return None

def update_to_latest():
    import requests
    print(f"{YELLOW}{BOLD}[*] Downloading latest version from GitHub...{RESET}")
    try:
        resp = requests.get(GITHUB_ZIP_URL, stream=True, timeout=30)
        if resp.status_code == 200:
            zip_bytes = io.BytesIO(resp.content)
            with zipfile.ZipFile(zip_bytes) as z:
                # Extract all files, overwrite existing
                for member in z.namelist():
                    if member.endswith('/'):
                        continue
                    target_path = os.path.join(PROJECT_ROOT, *member.split('/')[1:])
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, 'wb') as f:
                        f.write(z.read(member))
            print(f"{GREEN}{BOLD}[✓] Updated to latest version! Restarting...{RESET}")
            time.sleep(1)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            print(f"{RED}[!] Failed to download latest version (HTTP {resp.status_code}){RESET}")
    except Exception as e:
        print(f"{RED}[!] Update failed: {e}{RESET}")

def check_and_update():
    print(f"{YELLOW}{BOLD}[*] Checking for updates...{RESET}")
    latest = get_latest_version()
    if latest and latest != VERSION:
        print(f"{PINK}New version available: {latest} (current: {VERSION}){RESET}")
        update_to_latest()
    elif latest:
        print(f"{GREEN}{BOLD}[✓] You are running the latest version ({VERSION}){RESET}")
    else:
        print(f"{YELLOW}[!] Could not determine latest version. Continuing...{RESET}")

def main():
    print()
    check_and_update()
    check_dependencies()
    clear_screen()
    print_ascii_art()
    print()
    while True:
        try:
            cmdline = input(f"{PINK}> {RESET}")
            if cmdline.strip().lower() in ["exit", "quit", "q"]:
                clear_screen()
                print_ascii_art()
                print(f"{PINK}{BOLD}Goodbye!{RESET}")
                print()
                sys.exit(0)
            
            # Clear screen before showing command output (for all commands)
            clear_screen()
            print_ascii_art()
            run_command(cmdline)
            # Add spacing after command output
            print()
        except (KeyboardInterrupt, EOFError):
            clear_screen()
            print_ascii_art()
            print()  # Add space after ASCII art
            continue

if __name__ == "__main__":
    main()