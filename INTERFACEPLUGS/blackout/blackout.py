import requests
import socket
import os
import time
from datetime import datetime

class BlackoutESP32:
    def __init__(self, output_callback=None, print_ascii_art=None, YELLOW="\033[93m", GREEN="\033[38;2;180;189;104m", RED="\033[38;2;204;103;102m", PINK="\033[38;2;227;148;220m", RESET="\033[0m"):
        self.server_url = None
        self.esp32_connected = False
        self.output_callback = output_callback or (lambda msg, type='system': print(msg))
        self.print_ascii_art = print_ascii_art
        self.YELLOW = YELLOW
        self.GREEN = GREEN
        self.RED = RED
        self.PINK = PINK
        self.RESET = RESET

    def set_output_callback(self, callback):
        self.output_callback = callback

    def connect_to_server(self, server_ip):
        self.server_url = f"http://{server_ip}:3000"
        try:
            response = requests.get(f"{self.server_url}/scan-serial", timeout=5)
            if response.status_code == 200:
                self.output_callback(f"{self.GREEN}Connected to server at {server_ip}{self.RESET}", 'success')
                return True
            else:
                self.output_callback(f"{self.RED}Failed to connect to server: {response.text}{self.RESET}", 'error')
                return False
        except requests.exceptions.ConnectionError:
            self.output_callback(f"{self.RED}Could not connect to server at {server_ip}. Please check if the server is running.{self.RESET}", 'error')
            return False
        except requests.exceptions.Timeout:
            self.output_callback(f"{self.RED}Connection to {server_ip} timed out. Please check if the server is running.{self.RESET}", 'error')
            return False
        except Exception as e:
            self.output_callback(f"{self.RED}Error connecting to server: {str(e)}{self.RESET}", 'error')
            return False

    def scan_serial_ports(self):
        if not self.server_url:
            self.output_callback(f"{self.RED}Not connected to server. Use connect_to_server(server_ip) first{self.RESET}", 'error')
            return []
        try:
            response = requests.get(f"{self.server_url}/scan-serial")
            if response.status_code == 200:
                ports = response.json()
                if ports:
                    self.output_callback(f"{self.PINK}Available serial ports:{self.RESET}", 'system')
                    for port in ports:
                        self.output_callback(f"  {self.PINK}- {port['path']} ({port.get('manufacturer', 'Unknown')}){self.RESET}", 'system')
                    return ports
                else:
                    self.output_callback(f"{self.YELLOW}No serial ports found{self.RESET}", 'system')
                    return []
            else:
                self.output_callback(f"{self.RED}Failed to scan ports: {response.text}{self.RESET}", 'error')
                return []
        except Exception as e:
            self.output_callback(f"{self.RED}Error scanning ports: {str(e)}{self.RESET}", 'error')
            return []

    def connect_to_esp32(self, device):
        if not self.server_url:
            self.output_callback(f"{self.RED}Not connected to server. Use connect_to_server(server_ip) first{self.RESET}", 'error')
            return False
        try:
            response = requests.post(f"{self.server_url}/connect-serial", json={'device': device})
            if response.status_code == 200:
                self.esp32_connected = True
                self.output_callback(f"{self.GREEN}Connected to ESP32 on {device}{self.RESET}", 'success')
                return True
            else:
                self.output_callback(f"{self.RED}Failed to connect to ESP32: {response.text}{self.RESET}", 'error')
                return False
        except Exception as e:
            self.output_callback(f"{self.RED}Error connecting to ESP32: {str(e)}{self.RESET}", 'error')
            return False

    def send_esp32_command(self, command):
        if not self.server_url or not self.esp32_connected:
            self.output_callback(f"{self.RED}Not connected to ESP32. Connect first.{self.RESET}", 'error')
            return
        try:
            self.output_callback(f"{self.GREEN}Command sent: {command}{self.RESET}", 'success')
            self.output_callback(f"{self.PINK}Response:{self.RESET}", 'system')
            with requests.post(f"{self.server_url}/send-command", json={'command': command}, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]
                                self.output_callback(f"  {self.PINK}{data}{self.RESET}", 'system')
                else:
                    self.output_callback(f"{self.RED}Failed to send command: {response.text}{self.RESET}", 'error')
        except Exception as e:
            self.output_callback(f"{self.RED}Error sending command: {str(e)}{self.RESET}", 'error')  