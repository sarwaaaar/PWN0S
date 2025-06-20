#!/usr/bin/env python3
import subprocess
import shlex
import os
import sys
import getpass
import time
import signal
import threading
import json
import argparse

def is_ish_terminal():
    try:
        if 'ISH' in os.environ:
            return True
        with open('/proc/version', 'r') as f:
            return 'ish' in f.read().lower()
    except:
        return False

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[38;2;204;103;102m"
PINK = "\033[38;2;227;148;220m"
YELLOW = "\033[38;2;222;147;95m"
GREEN = "\033[38;2;180;189;104m"
AFB3B5 = "\033[38;2;175;179;181m"
VERSION = "0.3.9"

# Read ASCII art from shared file
SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))
ASCII_ART_PATH = os.path.join(SCRIPT_ROOT, '..', '..', 'ascii.txt')
try:
    with open(ASCII_ART_PATH, 'r', encoding='utf-8') as f:
        ASCII_ART = f.read()
except Exception:
    ASCII_ART = ''

def clear_screen():
    if is_ish_terminal():
        print("\033[2J\033[H", end="")
        print("\033[3J", end="")
        print("\033c", end="")
        print("\n" * 3)
        sys.stdout.flush()
        time.sleep(0.05)
    else:
        os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()

def print_ascii_art():
    print(ASCII_ART)

def show_loading_indicator(message, duration=2):
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duration
    while time.time() < end_time:
        for char in spinner:
            if time.time() >= end_time:
                break
            print(f"\r{YELLOW}[~] {message} {char}{RESET}", end='', flush=True)
            time.sleep(0.1)
    print("\r" + " " * (len(message) + 10) + "\r", end='', flush=True)

def create_config_file(username, ip, password):
    """Create or update config.json file with provided credentials"""
    config_path = os.path.join(SCRIPT_ROOT, 'config.json')
    config = {
        "username": username,
        "ip": ip,
        "password": password
    }
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"{GREEN}[✓] Config file created/updated: {config_path}{RESET}")
        return True
    except Exception as e:
        print(f"{RED}[!] Failed to create config file: {str(e)}{RESET}")
        return False

def connect_ssh(host, password):
    try:
        if '@' not in host:
            print(f"{RED}[!] Invalid host format. Use: user@host{RESET}")
            return
        clear_screen()
        print_ascii_art()
        print(f"{PINK}Preparing SSH connection to {host}...{RESET}")
        show_loading_indicator(f"Connecting to {host}...", duration=2)
        if is_ish_terminal():
            ssh_cmd = f"sshpass -p {shlex.quote(password)} ssh -o StrictHostKeyChecking=no {host}"
            process = subprocess.Popen(
                ssh_cmd,
                shell=True,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                universal_newlines=True
            )
            process.wait()
        else:
            ssh_cmd = [
                "sshpass", "-p", password,
                "ssh", "-o", "StrictHostKeyChecking=no", host
            ]
            import pty
            pty.spawn(ssh_cmd)
        clear_screen()
        print_ascii_art()
        print(f"{PINK}SSH session ended.{RESET}")
    except KeyboardInterrupt:
        print(f"\n{PINK}SSH session terminated.{RESET}")
    except Exception as e:
        print(f"{RED}[!] Connection error: {str(e)}{RESET}")

def print_usage():
    print(f"{BOLD}{PINK}deck - SSH Connection Manager{RESET}")
    print(f"{YELLOW}Usage:{RESET}")
    print(f"  deck                                    # Use existing config.json")
    print(f"  deck -username <user> -ip <ip> -password <pass>  # Set credentials and connect")
    print(f"  deck -h                                 # Show this help")
    print()
    print(f"{YELLOW}Examples:{RESET}")
    print(f"  deck")
    print(f"  deck -username admin -ip 192.168.1.100 -password mypass123")
    print()
    print(f"{YELLOW}Configuration:{RESET}")
    print(f"  Config file: {os.path.join(SCRIPT_ROOT, 'config.json')}")
    print(f"  Format: {{\"username\": \"user\", \"ip\": \"ip\", \"password\": \"pass\"}}")

def main():
    parser = argparse.ArgumentParser(description="SSH Connection Manager", add_help=False)
    parser.add_argument("-username", type=str, help="SSH username")
    parser.add_argument("-ip", type=str, help="Target IP address")
    parser.add_argument("-password", type=str, help="SSH password")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message")
    
    # Check for unknown args
    known_opts = ['-username', '-ip', '-password', '-h', '--help']
    for arg in sys.argv[1:]:
        if arg.startswith('-') and arg not in known_opts and not arg.startswith('--'):
            print(f"{RED}[!] Unknown option '{arg}'{RESET}")
            print_usage()
            sys.exit(1)
    
    args = parser.parse_args()
    
    if args.help:
        print_usage()
        sys.exit(0)
    
    # If credentials provided via command line
    if args.username and args.ip and args.password:
        print(f"{PINK}Setting up SSH connection with provided credentials...{RESET}")
        if create_config_file(args.username, args.ip, args.password):
            user_host = f"{args.username}@{args.ip}"
            connect_ssh(user_host, args.password)
        else:
            sys.exit(1)
        return
    
    # Use existing config.json
    clear_screen()
    config_path = os.path.join(SCRIPT_ROOT, 'config.json')
    if not os.path.exists(config_path):
        print(f"{RED}[!] config.json not found in {SCRIPT_ROOT}{RESET}")
        print(f"{YELLOW}Please create a config.json with username, ip, and password, or use command line arguments.{RESET}")
        print()
        print_usage()
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        username = config.get('username')
        ip = config.get('ip')
        password = config.get('password')
        if not username or not ip or not password:
            print(f"{RED}[!] config.json must contain username, ip, and password.{RESET}")
            sys.exit(1)
        user_host = f"{username}@{ip}"
        print(f"{PINK}Attempting SSH connection to {user_host}...{RESET}")
        connect_ssh(user_host, password)
    except Exception as e:
        print(f"{RED}[!] Failed to read config.json: {str(e)}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()