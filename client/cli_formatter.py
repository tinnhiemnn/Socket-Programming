import sys
import time

# ANSI Color Codes
COLOR_RESET   = "\033[0m"
COLOR_BOLD    = "\033[1m"
COLOR_GREEN   = "\033[32m"
COLOR_CYAN    = "\033[36m"
COLOR_YELLOW  = "\033[33m"
COLOR_RED     = "\033[31m"
COLOR_BLUE    = "\033[34m"
COLOR_MAGENTA = "\033[35m"

def print_header():
    banner = f"""
{COLOR_CYAN}{COLOR_BOLD}==============================================================
   ____ Custom RDT FTP Client (TCP Control + UDP Data) ____
=============================================================={COLOR_RESET}
    """
    print(banner)

def print_status(message: str, level: str = "INFO"):
    if level == "SUCCESS":
        prefix = f"{COLOR_GREEN}[✓ SUCCESS]{COLOR_RESET}"
    elif level == "WARNING":
        prefix = f"{COLOR_YELLOW}[! WARNING]{COLOR_RESET}"
    elif level == "ERROR":
        prefix = f"{COLOR_RED}[✗ ERROR]{COLOR_RESET}"
    elif level == "NET":
        prefix = f"{COLOR_MAGENTA}[⇄ NETWORK]{COLOR_RESET}"
    else:
        prefix = f"{COLOR_CYAN}[i INFO]{COLOR_RESET}"
    
    print(f"{prefix} {message}")

def print_progress_bar(transferred: int, total: int, speed_bps: float, bar_length: int = 30):
    if total is None or total <= 0:
        trans_str = format_bytes(transferred)
        speed_str = f"{format_bytes(speed_bps)}/s"
        sys.stdout.write(f"\r   Downloading: {trans_str} received | Speed: {speed_str}  ")
        sys.stdout.flush()
        sys.stdout.write("\n")
        return

    percent = min(1.0, transferred / total)
    progress = int(bar_length * percent)
    bar = f"{COLOR_GREEN}{'█' * progress}{COLOR_RESET}{'░' * (bar_length - progress)}"
    percentage_str = f"{percent * 100:6.2f}%"
    
    # Format size display (Bytes / KB / MB)
    trans_str = format_bytes(transferred)
    total_str = format_bytes(total) if total > 0 else "Unknown"
    speed_str = f"{format_bytes(speed_bps)}/s"

    sys.stdout.write(
        f"\r   Progress: [{bar}] {percentage_str} | {trans_str}/{total_str} | Speed: {speed_str} "
    )
    sys.stdout.flush()
    if transferred >= total and total > 0:
        sys.stdout.write("\n")

def format_bytes(size: float) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:6.1f} {unit}"
        size /= 1024.0
    return f"{size:6.1f} TB"