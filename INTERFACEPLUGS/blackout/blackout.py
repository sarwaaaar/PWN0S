import requests
import socket
import os
import time
from datetime import datetime

class BlackoutESP32:
    def __init__(self, output_callback=None):
        self.server_url = None
        self.esp32_connected = False
        self.output_callback = output_callback or (lambda msg, type='system': print(msg))

    def set_output_callback(self, callback):
        self.output_callback = callback

    def connect_to_server(self, server_ip):
        self.server_url = f"http://{server_ip}:3000"
        try:
            response = requests.get(f"{self.server_url}/scan-serial", timeout=5)
            if response.status_code == 200:
                self.output_callback(f"Connected to server at {server_ip}", 'success')
                return True
            else:
                self.output_callback(f"Failed to connect to server: {response.text}", 'error')
                return False
        except requests.exceptions.ConnectionError:
            self.output_callback(f"Could not connect to server at {server_ip}. Please check if the server is running.", 'error')
            return False
        except requests.exceptions.Timeout:
            self.output_callback(f"Connection to {server_ip} timed out. Please check if the server is running.", 'error')
            return False
        except Exception as e:
            self.output_callback(f"Error connecting to server: {str(e)}", 'error')
            return False

    def scan_serial_ports(self):
        if not self.server_url:
            self.output_callback("Not connected to server. Use connect_to_server(server_ip) first", 'error')
            return []
        try:
            response = requests.get(f"{self.server_url}/scan-serial")
            if response.status_code == 200:
                ports = response.json()
                if ports:
                    self.output_callback("Available serial ports:", 'system')
                    for port in ports:
                        self.output_callback(f"  - {port['path']} ({port.get('manufacturer', 'Unknown')})", 'system')
                    return ports
                else:
                    self.output_callback("No serial ports found", 'system')
                    return []
            else:
                self.output_callback(f"Failed to scan ports: {response.text}", 'error')
                return []
        except Exception as e:
            self.output_callback(f"Error scanning ports: {str(e)}", 'error')
            return []

    def connect_to_esp32(self, device):
        if not self.server_url:
            self.output_callback("Not connected to server. Use connect_to_server(server_ip) first", 'error')
            return False
        try:
            response = requests.post(f"{self.server_url}/connect-serial", json={'device': device})
            if response.status_code == 200:
                self.esp32_connected = True
                self.output_callback(f"Connected to ESP32 on {device}", 'success')
                return True
            else:
                self.output_callback(f"Failed to connect to ESP32: {response.text}", 'error')
                return False
        except Exception as e:
            self.output_callback(f"Error connecting to ESP32: {str(e)}", 'error')
            return False

    def send_esp32_command(self, command):
        if not self.server_url or not self.esp32_connected:
            self.output_callback("Not connected to ESP32. Connect first.", 'error')
            return
        try:
            self.output_callback(f"Command sent: {command}", 'success')
            self.output_callback("Response:", 'system')
            with requests.post(f"{self.server_url}/send-command", json={'command': command}, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]
                                self.output_callback(f"  {data}", 'system')
                else:
                    self.output_callback(f"Failed to send command: {response.text}", 'error')
        except Exception as e:
            self.output_callback(f"Error sending command: {str(e)}", 'error')  