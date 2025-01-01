import sys
import time
import threading
from colorama import Fore, Style

class DownloadAnimator:
    def __init__(self, package_name, installer):
        self.package_name = package_name
        self.installer = installer
        self.is_running = False
        self.progress = 0
        self.thread = None
        self.speed = 0.1  # Controls animation speed
        self.completed = False
        
    def update_progress(self, amount=1):
        """Update the progress bar by a specific amount"""
        self.progress += amount
        if self.progress > 100:
            self.progress = 100
            
    def _animate(self):
        """Animation loop that runs in a separate thread"""
        while self.is_running and self.progress < 100:
            # Clear the current line
            sys.stdout.write('\r')
            
            # Calculate bar segments - simple line progress bar
            bar_width = 30
            filled_length = int(bar_width * self.progress / 100)
            bar = '█' * filled_length + '░' * (bar_width - filled_length)
            
            # Format the progress message - single line only
            message = f"{Fore.CYAN}[Aegis] Installing {self.package_name} via {self.installer} {Fore.GREEN}[{bar}] {self.progress}%"
            
            # Print the progress bar
            sys.stdout.write(message)
            sys.stdout.flush()
            
            # Simulate random progress
            if not self.completed:
                self.update_progress(1 + (time.time() % 3))
            
            time.sleep(self.speed)
        
        # Final update when complete
        if self.completed:
            sys.stdout.write('\r')
            bar = '█' * bar_width
            message = f"{Fore.CYAN}[Aegis] Installing {self.package_name} via {self.installer} {Fore.GREEN}[{bar}] 100%{Style.RESET_ALL}"
            sys.stdout.write(message + "\n")
        
    def start(self):
        """Start the animation in a separate thread"""
        self.is_running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self, success=True):
        """Stop the animation"""
        self.completed = success
        if success:
            self.progress = 100
        time.sleep(0.5)  # Let the animation finish
        self.is_running = False
        if self.thread:
            self.thread.join()
        
        # Print final message
        print()
        if success:
            print(f"{Fore.GREEN}[Aegis] Successfully installed {self.package_name}!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[Aegis] Failed to install {self.package_name}.{Style.RESET_ALL}")