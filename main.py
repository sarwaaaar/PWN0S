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

VERSION = "0.0.7"

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[38;2;204;103;102m"
PINK = "\033[38;2;227;148;220m"
YELLOW = "\033[93m"
GREEN = "\033[38;2;102;204;102m"

# Command mapping: full command to short form
COMMAND_ALIASES = {
    "quickhack": "qh",
    "daemon": "d",
    "interfaceplug": "ip",
    "exit": "q",
    "quit": "q",
    "clear": "c",
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
    print(f"{BOLD}{PINK}Command Guide:{RESET}")
    print(f"{BOLD}{PINK}Main Commands:{RESET}")
    for c in COMMAND_ALIASES:
        print(f"  {PINK}{c:<14}{RESET} {YELLOW}(short: {COMMAND_ALIASES[c]}){RESET}")
    print(f"\n{BOLD}{PINK}Subcommands:{RESET}")
    print(f"  {PINK}quickhack{RESET} [ {YELLOW}shortcirc (sc), ping (pg){RESET} ]")
    print(f"    {YELLOW}shortcirc methods:{RESET} SMS (s), EMAIL (e), NTP (n), UDP (u), SYN (sy), ICMP (i), POD (p), MEMCACHED (m), HTTP (h), SLOWLORIS (sl)")
    print(f"    {YELLOW}ping options:{RESET} IP Tracker (ip), Show Your IP (sip), Phone Number Tracker (pn), Username Tracker (ut), Exit (q), {PINK}seeker{RESET}")
    print(f"    {YELLOW}seeker:{RESET} Run with: {PINK}python QUICKHACKS/ping/seeker.py -t <template_num> [options]{RESET}")
    print(f"{YELLOW}Note:{RESET} Commands other than quickhack, daemon, and interfaceplug must start with a dash (-).\n")

def suggest_command(user_cmd, valid_cmds):
    matches = difflib.get_close_matches(user_cmd, valid_cmds, n=3, cutoff=0.5)
    if matches:
        print(f"{YELLOW}Did you mean:{RESET}")
        for m in matches:
            short = ''
            if m in COMMAND_ALIASES:
                short = f" (short: {COMMAND_ALIASES[m]})"
            elif m in SHORT_TO_FULL:
                short = f" (full: {SHORT_TO_FULL[m]})"
            print(f"  {PINK}{m}{RESET}{YELLOW}{short}{RESET}")
    else:
        print(f"{YELLOW}No similar commands found.{RESET}")

def print_shortcirc_guide():
    print(f"{BOLD}{PINK}shortcirc Command Options:{RESET}")
    print(f"  -target    (Target ip:port, url or phone)")
    print(f"  -method    (Attack method: SMS (s), EMAIL (e), NTP (n), UDP (u), SYN (sy), ICMP (i), POD (p), MEMCACHED (m), HTTP (h), SLOWLORIS (sl))")
    print(f"  -time      (Attack duration in seconds)")
    print(f"  -threads   (Threads count)")
    print(f"  -h         (Help)")

def print_ping_guide():
    print(f"{BOLD}{PINK}ping Command Options:{RESET}")
    print(f"  -ip      (IP Tracker)")
    print(f"  -sip     (Show Your IP)")
    print(f"  -pn      (Phone Number Tracker)")
    print(f"  -ut      (Username Tracker)")
    print(f"  -h       (Help)")
    print(f"  -q       (Exit)")

def print_seeker_guide():
    print(f"{BOLD}{PINK}seeker Command Options:{RESET}")
    print(f"  -k,  --kml <filename>         KML filename")
    print(f"  -p,  --port <port>            Web server port [Default: 8080]")
    print(f"  -u,  --update                 Check for updates")
    print(f"  -v,  --version                Prints version")
    print(f"  -t,  --template <num>         Load template and loads parameters from env variables (required)")
    print(f"  -d,  --debugHTTP <bool>       Disable HTTPS redirection for testing only")
    print(f"  -tg, --telegram <token:chatId> Telegram bot API token [Format: token:chatId]")
    print(f"  -wh, --webhook <url>          Webhook URL [POST method & unauthenticated]")
    print()

def suggest_subcommand_option(user_opt, valid_opts):
    matches = difflib.get_close_matches(user_opt, valid_opts, n=3, cutoff=0.5)
    if matches:
        print(f"{YELLOW}Did you mean:{RESET}")
        for m in matches:
            print(f"  {PINK}{m}{RESET}")
    else:
        print(f"{YELLOW}No similar options found.{RESET}")

def run_command(cmdline):
    parts = cmdline.strip().split()
    if not parts:
        return
    cmd = parts[0].lower()
    # List of supported basic terminal commands
    BASIC_TERMINAL_COMMANDS = [
        'ls', 'pwd', 'cat', 'echo', 'mkdir', 'rm', 'touch', 'cp', 'mv', 'whoami', 'date', 'head', 'tail', 'grep', 'find', 'chmod', 'chown', 'rmdir', 'tree', 'df', 'du', 'which', 'uname', 'ps', 'kill', 'top', 'clear'
    ]
    # If the command is a basic terminal command, execute it directly
    if cmd in BASIC_TERMINAL_COMMANDS:
        try:
            result = subprocess.run(parts, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(f"{RED}{result.stderr}{RESET}", end='')
        except Exception as e:
            print(f"{RED}{BOLD}[!] Failed to execute command: {e}{RESET}")
        return
    # Map short form to full command if needed
    if cmd in SHORT_TO_FULL:
        cmd = SHORT_TO_FULL[cmd]
        parts[0] = cmd
    # Only these commands can be used without a dash
    allowed_no_dash = ["quickhack", "daemon", "interfaceplug", "exit", "quit", "clear"] + list(SHORT_TO_FULL.keys())
    if cmd not in allowed_no_dash and not cmd.startswith("-"):
        print(f"{RED}{BOLD}✗ Error:{RESET} {YELLOW}Unknown command '{cmd}'.{RESET}\n")
        suggest_command(cmd, COMMANDS)
        print()
        print_command_guide()
        return
    # If command starts with a dash, strip it for processing
    if cmd.startswith("-"):
        cmd = cmd[1:]
        parts[0] = cmd
        if cmd in SHORT_TO_FULL:
            cmd = SHORT_TO_FULL[cmd]
            parts[0] = cmd
    if cmd != "clear":
        clear_screen()
        print_ascii_art()
    if cmd == "quickhack":
        if len(parts) < 2:
            print(f"{BOLD}{RED}Usage: quickhack -<tool> [args]{RESET}")
            print(f"{BOLD}{PINK}Example:{RESET} quickhack -setoolkit -h\n")
            print_command_guide()
            return
        tool = parts[1].lstrip('-')
        SUBCOMMAND_ALIASES = {"shortcirc": "sc", "ping": "pg"}
        SHORT_TO_SUB = {v: k for k, v in SUBCOMMAND_ALIASES.items()}
        all_subs = list(SUBCOMMAND_ALIASES.keys()) + list(SHORT_TO_SUB.keys())
        if tool in SHORT_TO_SUB:
            tool = SHORT_TO_SUB[tool]
            parts[1] = tool
        if tool in all_subs:
            if tool == "shortcirc":
                valid_opts = ['-target', '-method', '-time', '-threads', '-h']
                for arg in parts[2:]:
                    if arg.startswith('-') and arg not in valid_opts and not arg.startswith('--'):
                        print(f"{RED}{BOLD}✗ Error:{RESET} {YELLOW}Unknown option '{arg}' for shortcirc.{RESET}\n")
                        suggest_subcommand_option(arg, valid_opts)
                        print()
                        print_shortcirc_guide()
                        print_command_guide()
                        return
            if tool == "ping":
                valid_opts = ['-ip', '-pn', '-ut', '-sip', '-h', '-q', '-seeker']
                is_seeker = '-seeker' in parts[2:]
                if is_seeker:
                    # Find the index of -seeker and pass all following args to seeker.py
                    seeker_index = parts.index('-seeker')
                    seeker_args = parts[seeker_index+1:]
                    with loading_state(message="Installing requirements for seeker...", duration=2, print_ascii_art=print_ascii_art):
                        pass
                    requirements = ["requests", "argparse", "packaging", "psutil"]
                    print(f"{YELLOW}{BOLD}[*] Installing requirements...{RESET}")
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + requirements, check=True)
                    except subprocess.CalledProcessError:
                        print(f"{RED}{BOLD}[!] Failed to install requirements. Aborting.{RESET}")
                        print()
                        return
                    with loading_state(message="Invoking seeker toolkit...", duration=2, print_ascii_art=print_ascii_art):
                        pass
                    script_path = os.path.join(PROJECT_ROOT, "QUICKHACKS", "ping", "seeker.py")
                    try:
                        subprocess.run([sys.executable, script_path] + seeker_args)
                    except FileNotFoundError:
                        print(f"{RED}{BOLD}[!] seeker script not found at {script_path}.{RESET}")
                    print()
                    return
                # Normal ping option validation if not seeker
                for arg in parts[2:]:
                    if arg.startswith('-') and arg not in valid_opts and not arg.startswith('--'):
                        print(f"{RED}{BOLD}✗ Error:{RESET} {YELLOW}Unknown option '{arg}' for ping.{RESET}\n")
                        suggest_subcommand_option(arg, valid_opts)
                        print()
                        print_ping_guide()
                        return
                # If help requested for seeker
                if is_seeker and ('-h' in parts[2:] or '--help' in parts[2:]):
                    print_seeker_guide()
                    return
            # Replace with full name for script invocation
            if tool == "shortcirc":
                with loading_state(message="Installing requirements for shortcirc...", duration=2, print_ascii_art=print_ascii_art):
                    pass
                requirements = ["requests", "scapy", "wget", "argparse", "colorama", "humanfriendly"]
                print(f"{YELLOW}{BOLD}[*] Installing requirements...{RESET}")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + requirements, check=True)
                except subprocess.CalledProcessError:
                    print(f"{RED}{BOLD}[!] Failed to install requirements. Aborting.{RESET}")
                    print()
                    return
                with loading_state(message="Invoking shortcirc toolkit...", duration=2, print_ascii_art=print_ascii_art):
                    pass
                script_path = os.path.join(PROJECT_ROOT, "QUICKHACKS", "shortcirc", "shortcirc.py")
                try:
                    subprocess.run([sys.executable, script_path] + parts[2:])
                except FileNotFoundError:
                    print(f"{RED}{BOLD}[!] shortcirc script not found at {script_path}.{RESET}")
                print()
                return
            if tool == "ping":
                if len(parts) > 2 and parts[2] == "-seeker":
                    with loading_state(message="Installing requirements for seeker...", duration=2, print_ascii_art=print_ascii_art):
                        pass
                    requirements = ["requests", "argparse", "packaging", "psutil"]
                    print(f"{YELLOW}{BOLD}[*] Installing requirements...{RESET}")
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + requirements, check=True)
                    except subprocess.CalledProcessError:
                        print(f"{RED}{BOLD}[!] Failed to install requirements. Aborting.{RESET}")
                        print()
                        return
                    with loading_state(message="Invoking seeker toolkit...", duration=2, print_ascii_art=print_ascii_art):
                        pass
                    script_path = os.path.join(PROJECT_ROOT, "QUICKHACKS", "ping", "seeker.py")
                    try:
                        subprocess.run([sys.executable, script_path] + parts[3:])
                    except FileNotFoundError:
                        print(f"{RED}{BOLD}[!] seeker script not found at {script_path}.{RESET}")
                    print()
                    return
                with loading_state(message="Installing requirements for ping...", duration=2, print_ascii_art=print_ascii_art):
                    pass
                requirements = ["requests", "phonenumbers"]
                print(f"{YELLOW}{BOLD}[*] Installing requirements...{RESET}")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + requirements, check=True)
                except subprocess.CalledProcessError:
                    print(f"{RED}{BOLD}[!] Failed to install requirements. Aborting.{RESET}")
                    print()
                    return
                with loading_state(message="Invoking ping toolkit...", duration=2, print_ascii_art=print_ascii_art):
                    pass
                script_path = os.path.join(PROJECT_ROOT, "QUICKHACKS", "ping", "ping.py")
                try:
                    subprocess.run([sys.executable, script_path] + parts[2:])
                except FileNotFoundError:
                    print(f"{RED}{BOLD}[!] ping script not found at {script_path}.{RESET}")
                print()
                return
        # If not a known subcommand, treat as external tool
        with loading_state(message=f"Launching {tool}...", duration=2, print_ascii_art=print_ascii_art):
            pass
        try:
            subprocess.run([tool] + parts[2:])
        except FileNotFoundError:
            print(f"{RED}{BOLD}[!] Tool '{tool}' not found.{RESET} {YELLOW}Make sure it's installed in your environment or in your PATH.{RESET}")
        print()
        return
    elif cmd == "daemon":
        if len(parts) > 1 and parts[1] == "-rabids":
            rabdis_path = os.path.join(PROJECT_ROOT, "DAEMONS", "rabids", "rabids.py")
            args = [sys.executable, rabdis_path] + parts[2:]
            with loading_state(message="Automating payload embedding and compilation...", duration=2, print_ascii_art=print_ascii_art):
                pass
            try:
                subprocess.run(args, check=True)
            except subprocess.CalledProcessError:
                print(f"{RED}{BOLD}[!] rabdis.py failed to run properly.{RESET}")
            print()
            return
        if len(parts) > 1 and parts[1] == "-filedaemon" and len(parts) > 2 and parts[2] == "-start":
            filedaemon_path = os.path.join(PROJECT_ROOT, "DAEMONS", "filedaemon", "filedaemon.py")
            args = [sys.executable, filedaemon_path, "-start"]
            with loading_state(message="Starting filedaemon server...", duration=2, print_ascii_art=print_ascii_art):
                pass
            try:
                subprocess.run(args, check=True)
            except subprocess.CalledProcessError:
                print(f"{RED}{BOLD}[!] filedaemon.py failed to run properly.{RESET}")
            print()
            return
        with loading_state(message="Starting daemon...", duration=2, print_ascii_art=print_ascii_art):
            pass
        print(f"{BOLD}{PINK}[*] Daemon command invoked! (stub){RESET}")
        print()
    elif cmd == "interfaceplug" and len(parts) > 1 and parts[1] in ["-blackout", "-b"]:
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
        valid_blackout_opts = ["-connect", "-c", "-scan", "-send", "-p", "-pw"]
        if not args or (args[0] not in valid_blackout_opts and not (args[0] in ["-connect", "-c"] and len(args) > 1 and args[1] in ["-p", "-pw"])):
            print(f"{RED}{BOLD}✗ Error:{RESET} {YELLOW}Unknown blackout subcommand or option: '{' '.join(args)}'{RESET}\n")
            suggest_subcommand_option(args[0] if args else '', valid_blackout_opts)
            print()
            print(f"{BOLD}{PINK}interfaceplug -blackout options:{RESET}\n  -connect <server_ip>\n  -scan\n  -connect -p <device>\n  -send <command>\n")
            print_command_guide()
            return
        if args[0] in ["-connect", "-c"] and len(args) == 2:
            with loading_state(message=f"Connecting to server at {args[1]}...", duration=2, print_ascii_art=print_ascii_art):
                blackout.connect_to_server(args[1])
        elif args[0] == "-scan":
            with loading_state(message="Scanning serial ports...", duration=2, print_ascii_art=print_ascii_art):
                blackout.scan_serial_ports()
        elif args[0] in ["-connect", "-c"] and len(args) > 2 and args[1] in ["-p", "-pw"]:
            with loading_state(message=f"Connecting to ESP32 on {args[2]}...", duration=2, print_ascii_art=print_ascii_art):
                blackout.connect_to_esp32(args[2])
        elif args[0] == "-send" and len(args) > 1:
            with loading_state(message=f"Sending command: {' '.join(args[1:])}...", duration=2, print_ascii_art=print_ascii_art):
                blackout.send_esp32_command(' '.join(args[1:]))
        else:
            print(f"{RED}Usage: interfaceplug -blackout -connect <server_ip> | -scan | -connect -p <device> | -send <command>{RESET}")
        return
    elif cmd == "clear":
        clear_screen()
        print_ascii_art()
        print(f"{YELLOW}Screen cleared!{RESET}")
        print()
    elif cmd in ["exit", "quit", "q"]:
        clear_screen()
        print_ascii_art()
        print(f"{PINK}{BOLD}Bye!{RESET}")
        print()
        sys.exit(0)
    else:
        print(f"{RED}{BOLD}✗ Error:{RESET} {YELLOW}Unknown command '{cmd}'.{RESET}\n")
        suggest_command(cmd, COMMANDS)
        print()
        print_command_guide()
        print()

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
    check_and_update()
    check_dependencies()
    clear_screen()
    print_ascii_art()
    while True:
        try:
            cmdline = input(f"{PINK}{BOLD}>{RESET} ")
            run_command(cmdline)
        except (KeyboardInterrupt, EOFError):
            clear_screen()
            print_ascii_art()
            continue

if __name__ == "__main__":
    main()