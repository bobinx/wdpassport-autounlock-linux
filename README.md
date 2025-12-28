# WD Passport Auto Unlock & Mount

Scripts to automatically unlock and mount a WD Passport HDD on Linux

## Prerequisites

1.  **Clone this repository**:
    ```bash
    git clone --recursive <URL_TO_THIS_REPO>
    cd wdpassport-autounlock-linux
    ```
    *If you already cloned it without `--recursive`, run:*
    ```bash
    git submodule update --init
    ```

2.  **Dependencies**: Install Python pip and sg3-utils.
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-pip sg3-utils
    ```

## Configuration

Open `wd_auto_unlock.py` in a text editor and check the top configuration section:

```python
# --- CONFIGURATION ---
PASSWORD = "password"         # <--- Change to your actual HDD password
DRIVE_UUID = "88E2-42DF"      # <--- UUID of your partition (run `sudo blkid`). Used to identify the drive after unlock.
MOUNT_POINT = "/media/WD"     # <--- Desired mount point
```

## Installation

Run the following commands to install the script and services:

1.  **Install Files**
    Create a directory in `/usr/local/bin` and copy the files there:
    ```bash
    sudo mkdir -p /usr/local/bin/wd-auto-unlock
    sudo cp wd_auto_unlock.py /usr/local/bin/wd-auto-unlock/
    
    # Copy the required utility scripts from the submodule
    sudo cp -R wdpassport-utils /usr/local/bin/wd-auto-unlock/
    
    # Make executable
    sudo chmod +x /usr/local/bin/wd-auto-unlock/wd_auto_unlock.py
    ```

2.  **Install Systemd Service & Timer**
    *   **Service**: Defines *how* the unlock runs. (Required)
    *   **Timer**: Delays execution by 30s on boot. (Optional: Use if you want to ensure the system is fully settled before mounting on boot).
    ```bash
    sudo cp wd-unlock.service /etc/systemd/system/
    # Optional: Install timer if you want a boot-time delay
    sudo cp wd-unlock.timer /etc/systemd/system/
    ```

3.  **Install Udev Rule (for hot-plugging)**
    ```bash
    sudo cp 99-wd-passport.rules /etc/udev/rules.d/
    ```

4.  **Activate**
    ```bash
    sudo systemctl daemon-reload
    sudo udevadm control --reload-rules
    
    sudo systemctl enable --now wd-unlock.timer


## Troubleshooting

**1. Service didn't start?**
Check the logs:
```bash
sudo journalctl -u wd-unlock.service
```

**2. Udev rule not triggering?**
Monitor udev events in real-time found by the kernel:
```bash
sudo udevadm monitor --environment --udev
```
Then plug in the drive. You should see events. If you don't see `TAGS=:systemd:` or `Use of: wd-unlock.service` in the output, verify:
*   The `model` and `vendor` in `99-wd-passport.rules` match your drive (check with `udevadm info -a /dev/sdb`).
*   You reloaded rules: `sudo udevadm control --reload-rules`.


## Uninstall

To remove the automation:

1.  **Stop and Disable Services**
    ```bash
    sudo systemctl stop wd-unlock.service wd-unlock.timer
    sudo systemctl disable wd-unlock.service wd-unlock.timer
    ```

2.  **Remove Files**
    ```bash
    sudo rm /etc/systemd/system/wd-unlock.service
    sudo rm /etc/systemd/system/wd-unlock.timer
    sudo rm /etc/udev/rules.d/99-wd-passport.rules
    sudo rm -rf /usr/local/bin/wd-auto-unlock
    ```

3.  **Reload Daemons**
    ```bash
    sudo systemctl daemon-reload
    sudo udevadm control --reload-rules
    ```
    