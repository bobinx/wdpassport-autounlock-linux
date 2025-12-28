#!/usr/bin/env python3
import sys
import os
import time
import getpass
import importlib.util
import subprocess
import argparse
from unittest.mock import MagicMock

# --- CONFIGURATION ---
# Default password - change this if your drive password differs
PASSWORD = "password"
# Drive UUID (blkid)
DRIVE_UUID = "88E2-42DF" 
# Target Mount Point
MOUNT_POINT = "/media/WD"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# Expecting wdpassport-utils.py to be in the same folder as this script
REPO_PATH = SCRIPT_DIR
SCRIPT_PATH = os.path.join(REPO_PATH, "wdpassport-utils/wdpassport-utils.py")
# -----------------

def setup_environment():
    """Sets up the environment to import the wdpassport-utils script."""
    if not os.path.exists(SCRIPT_PATH):
        print(f"Error: {SCRIPT_PATH} not found.")
        sys.exit(1)

    sys.path.append(REPO_PATH)

    # Mock getpass to return our password automatically
    getpass.getpass = MagicMock(return_value=PASSWORD)

def import_wd_utils():
    """Imports the wdpassport-utils script as a module."""
    try:
        spec = importlib.util.spec_from_file_location("wdpassport_utils", SCRIPT_PATH)
        wd_utils = importlib.util.module_from_spec(spec)
        sys.modules["wdpassport_utils"] = wd_utils
        spec.loader.exec_module(wd_utils)
        return wd_utils
    except ImportError as e:
        print(f"Failed to import utility: {e}")
        sys.exit(1)

def unlock_device(wd_utils):
    """Runs the unlock routine."""
    print("--- Checking Lock Status ---")
    # We simulate calling the script with arguments
    sys.argv = [SCRIPT_PATH, "--unlock"]
    try:
        wd_utils.main(sys.argv[1:])
    except SystemExit as e:
        if e.code != 0:
            print(f"Unlock/Status check exited with code {e.code}")
    except Exception as eobj:
        print(f"Error during unlock: {eobj}")

def wait_for_device(uuid, timeout=30):
    """Waits for the block device with the given UUID to appear."""
    print(f"--- Waiting for Partition UUID={uuid} ---")
    device_path = f"/dev/disk/by-uuid/{uuid}"
    
    for i in range(timeout):
        if os.path.exists(device_path):
            print(f"Found device at {device_path}")
            return True
        if i % 5 == 0:
            print(f"Waiting for device... ({i}/{timeout})")
        time.sleep(1)
    
    return False

def mount_device(uuid, mount_point):
    """Mounts the device by UUID."""
    print(f"--- Mounting to {mount_point} ---")

    if os.path.ismount(mount_point):
        print(f"{mount_point} is already mounted.")
        return True

    if not os.path.exists(mount_point):
        try:
            os.makedirs(mount_point, exist_ok=True)
            print(f"Created mount point {mount_point}")
        except OSError as e:
            print(f"Error creating mount point: {e}")
            return False

    cmd = ["mount", f"UUID={uuid}", mount_point]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Mount successful.")
        return True
    else:
        print(f"Mount failed: {result.stderr.strip()}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Auto Unlock and Mount WD Passport")
    parser.add_argument("--timeout", type=int, default=30, help="Max seconds to wait for device UUID (not a delay)")
    args = parser.parse_args()

    setup_environment()
    wd_utils = import_wd_utils()

    unlock_device(wd_utils)
    
    # Tiny pause to ensure kernel device state settles
    time.sleep(0.5)
    os.system("udevadm trigger") # Prompt kernel to re-scan
    
    if wait_for_device(DRIVE_UUID, timeout=args.timeout):
        mount_device(DRIVE_UUID, MOUNT_POINT)
    else:
        print("Device not found. Is it connected?")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we run as root
    if os.geteuid() != 0:
        print("This script must be run as root.")
        sys.exit(1)
    main()
