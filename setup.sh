#!/bin/bash

# Warna untuk output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== App Monitor Auto Installer ===${NC}"

# 1. Update & Install Dependencies
echo -e "${GREEN}[1/3] Memperbarui sistem & menginstal Python...${NC}"
pkg update && pkg upgrade -y
pkg install python -y

# 2. Install Library Python
echo -e "${GREEN}[2/3] Menginstal library requests...${NC}"
pip install requests

# 3. Memberikan Izin Eksekusi
chmod +x monitor.py

echo -e "${GREEN}[3/3] Selesai!${NC}"
echo -e "Silakan jalankan perintah berikut untuk mulai:"
echo -e "${BLUE}python monitor.py${NC}"
