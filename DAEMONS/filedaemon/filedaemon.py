import sys
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import shutil
import difflib

RED = "\033[38;2;204;103;102m"
GREEN = "\033[38;2;102;204;103m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

USAGE = f"""
{YELLOW}{BOLD}Usage:{RESET}
  python filedaemon.py -start | -s    # Start HTTP server for 'dir' folder
  python filedaemon.py -clean  | -c   # Remove all contents from 'dir' folder
"""

FILEDAEMON_OPTS = ['-start', '-s', '-clean', '-c']

def print_error(msg):
    print(f"{RED}{BOLD}[ERROR]{RESET} {msg}")

def print_info(msg):
    print(f"{GREEN}{BOLD}[INFO]{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}{BOLD}[WARN]{RESET} {msg}")

def print_filedaemon_guide():
    print(f"{YELLOW}{BOLD}filedaemon Command Options:{RESET}")
    print(f"  -start   (Start HTTP server for 'dir' folder)")
    print(f"  -s       (Short for -start)")
    print(f"  -clean   (Remove all contents from 'dir' folder)")
    print(f"  -c       (Short for -clean)")
    print()

def suggest_filedaemon_option(user_opt, valid_opts):
    matches = difflib.get_close_matches(user_opt, valid_opts, n=3, cutoff=0.5)
    if matches:
        print(f"{YELLOW}Did you mean:{RESET}")
        for m in matches:
            print(f"  {BOLD}{m}{RESET}")
    else:
        print(f"{YELLOW}No similar options found.{RESET}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    serve_dir = os.path.join(base_dir, "dir")
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("-start", "-s"):
            # Serve the 'dir' directory
            try:
                if not os.path.isdir(serve_dir):
                    print_error(f"Directory not found: {serve_dir}")
                    sys.exit(1)
                os.chdir(serve_dir)
                port = 8000
                print_info(f"Serving {serve_dir} at http://localhost:{port}/ (Ctrl+C to stop)")
                httpd = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print_info("Server stopped by user.")
            except Exception as e:
                print_error(f"Failed to start server: {e}")
                sys.exit(1)
        elif arg in ("-clean", "-c"):
            # Remove all files and folders in 'dir'
            try:
                if not os.path.isdir(serve_dir):
                    print_error(f"Directory not found: {serve_dir}")
                    sys.exit(1)
                removed_any = False
                for entry in os.listdir(serve_dir):
                    entry_path = os.path.join(serve_dir, entry)
                    try:
                        if os.path.isfile(entry_path) or os.path.islink(entry_path):
                            os.remove(entry_path)
                            removed_any = True
                        elif os.path.isdir(entry_path):
                            shutil.rmtree(entry_path)
                            removed_any = True
                    except Exception as e:
                        print_warning(f"Failed to remove {entry_path}: {e}")
                if removed_any:
                    print_info(f"All contents removed from {serve_dir}.")
                else:
                    print_info(f"{serve_dir} is already empty.")
            except Exception as e:
                print_error(f"Failed to clean directory: {e}")
                sys.exit(1)
        else:
            print(f"{RED}{BOLD}✗ Error:{RESET} {YELLOW}Unknown option '{arg}' for filedaemon.{RESET}\n")
            suggest_filedaemon_option(arg, FILEDAEMON_OPTS)
            print()
            print_filedaemon_guide()
    else:
        print(USAGE)
        print_filedaemon_guide() 