#!/usr/bin/env bash
# Seconds since the user last touched the keyboard, mouse, or trackpad (macOS).
# Taking the foreground while this is small means fighting the user for the screen.
ioreg -c IOHIDSystem | awk '/HIDIdleTime/ { printf "%d\n", $NF / 1000000000; exit }'
