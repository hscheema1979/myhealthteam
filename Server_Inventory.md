# Server Inventory

*Last updated: 2025-12-09 (verified via SSH)*
*Updated: 2025-12-09 - Added Tailscale VPN to all servers*

## Overview

| Server | Role | IP | Tailscale IP | vCPU | RAM | Disk | OS | Status |
|--------|------|----|--------------|------|-----|------|----|--------|
| Server 1 (KVM2) | Heavy Lifter | 82.180.131.68 | 100.101.179.63 | 2 | 8 GB | 96 GB | Ubuntu 24.04.3 LTS | SSH accessible, Tailscale VPN active |
| Server 2 (KVM4) | Web App | 178.16.140.23 | 100.103.208.24 | 4 | 16 GB | 193 GB | Ubuntu 24.04.3 LTS | Fully operational with web app, monitoring, Portainer |
| Server 3 (Cloud VPS) | Agent0/AI | 62.146.175.96 | 100.64.197.32 | 4 | 8 GB | 193 GB | Ubuntu 24.04.3 LTS | Docker agents running, Tailscale VPN, Agent0 ready |
| Windows PC | Local Machine | 10.0.0.178 | 100.126.182.128 | - | - | - | Windows 11 | SSH server, monitoring system, tunnel ready |

## Server 1: srv1169614.hstgr.cloud (KVM2)

- **IP Address**: 82.180.131.68
- **Hostname**: srv1169614.hstgr.cloud
- **Hardware**: 2 vCPU, 8 GB RAM, 96 GB SSD
- **Operating System**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel**: Linux 6.8.0-87-generic
- **Open Ports**: 22 (SSH), 8550 (Python service), 1721 (monarx-agent), 53 (DNS)
- **Services**:
  - SSH (active)
  - Python application on port 8550
  - Monarx security agent
  - systemd-resolved
- **Docker**: Not installed/running
- **Notes**: Heavy Lifter role; ready for Docker/Portainer setup.

## Server 2: srv1167106.hstgr.cloud (KVM4)

- **IP Address**: 178.16.140.23
- **Hostname**: srv1167106.hstgr.cloud
- **Hardware**: 4 vCPU, 16 GB RAM, 193 GB SSD
- **Operating System**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel**: Linux 6.8.0-88-generic
- **Open Ports**: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8501 (Streamlit), 8502 (Monitoring), 8504 (unknown), 8000 (Portainer HTTP), 9443 (Portainer HTTPS), 36187 (Node.js), 44277 (containerd), 35309/46365/39709 (language servers)
- **Services**:
  - SSH
  - Nginx (reverse proxy, serves `care.myhealthteam.org`)
  - Streamlit (MyHealthTeam application) on port 8501 (behind Nginx)
  - Flask Monitoring Dashboard on port 8502 (real-time service monitoring)
  - Portainer CE on ports 8000/9443 (running 8 days)
  - Certbot for SSL certificate management
  - systemd services: `myhealthteam.service`, `nginx.service`
  - Auto-restart monitoring scripts (`service_monitor.py`, `auto_restart_monitor.py`)
- **Docker Containers**:
  - `portainer` (Up 8 days)
- **Domain**: `care.myhealthteam.org` points to this server.
- **Status**: Fully operational; monitoring dashboard accessible at `http://178.16.140.23:8502`.

## Server 3: vmi2954037.contabo.host (Cloud VPS 20 SSD)

- **IP Address**: 62.146.175.96
- **IPv6**: 2605:a141:2295:4037::1
- **Hostname**: vmi2954037.contabo.host
- **Hardware**: 4 vCPU, 12 GB RAM, 193 GB SSD
- **Operating System**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **Kernel**: Linux 6.8.0-88-generic
- **Open Ports**: 22 (SSH), 80 (nginx), 50001 (agent-zero), 50002 (agent-one), 36369 (containerd), 55057/33048 (tailscaled)
- **Services**:
  - SSH
  - Nginx on port 80
  - Docker with two running agents
  - Tailscale VPN
  - VSCode remote development configured (launch via `vscode_server3_dev.bat`)
- **Docker Containers**:
  - `agent-zero-1` (Up 2 days) - ports 22, 9000-9009, mapped to host port 50001
  - `agent-one-1` (Up 55 minutes) - ports 22, 9000-9009, mapped to host port 50002
- **Notes**: Monthly contract VPS; AI agents running; Tailscale VPN active.


## SSH Configuration

All servers are configured with SSH key authentication and are accessible via aliases in `~/.ssh/config`:
- `server1` → root@82.180.131.68
- `server2` → root@178.16.140.23
- `server3` → root@62.146.175.96

Root password is ``#Hsc9097534694 for Server 1 and Server 2, and `Hsc9097534694` (without `#`) for Server 3.

## References

- `PROJECT_LIVING_DOCUMENT.md` – overall project status
- `Server Setup Commands.md` – setup instructions
- `PROCESS_MANAGEMENT.md` – service management details
- `SERVER3_SETUP_SUMMARY.md` – Server 3 specifics

## Raw SSH Verification Data

### Server 1 Verification Command

```bash
ssh server1 "uname -a && cat /etc/os-release && free -h && df -h && ufw status verbose && ss -tulpn && docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'"
```

### Server 1 Verification Output

```
Linux srv1169614 6.8.0-87-generic #88-Ubuntu SMP PREEMPT_DYNAMIC Sat Oct 11 09:28:41 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
PRETTY_NAME="Ubuntu 24.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.3 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       612Mi       2.6Gi       1.0Mi       4.8Gi       7.2Gi
Swap:             0B          0B          0B
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           795M  1.1M  794M   1% /run
/dev/sda1        96G  7.5G   89G   8% /
tmpfs           3.9G   16K  3.9G   1% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/sda16      881M  119M  701M  15% /boot
/dev/sda15      105M  6.2M   99M   6% /boot/efi
tmpfs           795M   12K  795M   1% /run/user/0
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
8550                       ALLOW IN    Anywhere
22/tcp                     ALLOW IN    Anywhere
8550 (v6)                  ALLOW IN    Anywhere (v6)
22/tcp (v6)                ALLOW IN    Anywhere (v6)

Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
udp   UNCONN 0      0          127.0.0.1:1721       0.0.0.0:*    users:(("monarx-agent",pid=3733,fd=8))
udp   UNCONN 0      0         127.0.0.54:53         0.0.0.0:*    users:(("systemd-resolve",pid=524,fd=16))
udp   UNCONN 0      0      127.0.0.53%lo:53         0.0.0.0:*    users:(("systemd-resolve",pid=524,fd=14))
tcp   LISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*    users:(("systemd-resolve",pid=524,fd=15))
tcp   LISTEN 0      4096         0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=1861,fd=3),("systemd",pid=1,fd=198))
tcp   LISTEN 0      128          0.0.0.0:8550       0.0.0.0:*    users:(("python",pid=58359,fd=6),("python",pid=58359,fd=5),("python",pid=58349,fd=5))
tcp   LISTEN 0      4096       127.0.0.1:65529      0.0.0.0:*    users:(("monarx-agent",pid=3733,fd=10))
tcp   LISTEN 0      4096      127.0.0.54:53         0.0.0.0:*    users:(("systemd-resolve",pid=524,fd=17))
tcp   LISTEN 0      4096            [::]:22            [::]:*    users:(("sshd",pid=1861,fd=4),("systemd",pid=1,fd=199))
```

### Server 2 Verification Command

```bash
ssh server2 "uname -a && cat /etc/os-release && free -h && df -h && ufw status verbose && ss -tulpn && docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'"
```

### Server 2 Verification Output

```
Linux srv1167106 6.8.0-88-generic #89-Ubuntu SMP PREEMPT_DYNAMIC Sat Oct 11 01:02:46 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
PRETTY_NAME="Ubuntu 24.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.3 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
               total        used        free      shared  buff/cache   available
Mem:            15Gi       1.4Gi       7.4Gi       1.4Mi       7.2Gi        14Gi
Swap:             0B          0B          0B
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           1.6G  1.2M  1.6G   1% /run
/dev/sda1       193G   11G  183G   6% /
tmpfs           7.9G     0  7.9G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/sda16      881M  119M  701M  15% /boot
/dev/sda15      105M  6.2M   99M   6% /boot/efi
overlay         193G   11G  183G   6% /var/lib/docker/overlay2/948d6a1c2c4486079003acd454da343720c721edc53435826ad64ac7238199ab/merged
tmpfs           1.6G   16K  1.6G   1% /run/user/0
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
8501/tcp                   ALLOW IN    Anywhere
22/tcp                     ALLOW IN    Anywhere
80/tcp                     ALLOW IN    Anywhere
443/tcp                    ALLOW IN    Anywhere
8502/tcp                   ALLOW IN    Anywhere
# VPS Monitoring Dashboard
8504/tcp                   ALLOW IN    Anywhere
8501/tcp (v6)              ALLOW IN    Anywhere (v6)
22/tcp (v6)                ALLOW IN    Anywhere (v6)
80/tcp (v6)                ALLOW IN    Anywhere (v6)
443/tcp (v6)               ALLOW IN    Anywhere (v6)
8502/tcp (v6)              ALLOW IN    Anywhere (v6)
# VPS Monitoring Dashboard
8504/tcp (v6)              ALLOW IN    Anywhere (v6)

Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess
udp   UNCONN 0      0         127.0.0.54:53         0.0.0.0:*    users:(("systemd-resolve",pid=604,fd=16))
udp   UNCONN 0      0      127.0.0.53%lo:53         0.0.0.0:*    users:(("systemd-resolve",pid=604,fd=14))
udp   UNCONN 0      0          127.0.0.1:1721       0.0.0.0:*    users:(("monarx-agent",pid=4467,fd=7))
tcp   LISTEN 0      4096       127.0.0.1:44277      0.0.0.0:*    users:(("containerd",pid=921,fd=9))
tcp   LISTEN 0      511        127.0.0.1:36187      0.0.0.0:*    users:(("node",pid=404854,fd=21))
tcp   LISTEN 0      4096         0.0.0.0:8000       0.0.0.0:*    users:(("docker-proxy",pid=2046,fd=7))
tcp   LISTEN 0      4096       127.0.0.1:35309      0.0.0.0:*    users:(("language_server",pid=405025,fd=10))
tcp   LISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*    users:(("systemd-resolve",pid=604,fd=15))
tcp   LISTEN 0      4096       127.0.0.1:46365      0.0.0.0:*    users:(("language_server",pid=405025,fd=17))
tcp   LISTEN 0      4096         0.0.0.0:9443       0.0.0.0:*    users:(("docker-proxy",pid=2061,fd=7))
tcp   LISTEN 0      128          0.0.0.0:8504       0.0.0.0:*    users:(("python3",pid=272552,fd=3))
tcp   LISTEN 0      128          0.0.0.0:8502       0.0.0.0:*    users:(("python3",pid=238380,fd=3))
tcp   LISTEN 0      128          0.0.0.0:8501       0.0.0.0:*    users:(("streamlit",pid=331434,fd=6))
tcp   LISTEN 0      128          0.0.0.0:8550       0.0.0.0:*    users:(("python3",pid=227879,fd=3))
tcp   LISTEN 0      511          0.0.0.0:443        0.0.0.0:*    users:(("nginx",pid=273203,fd=5),("nginx",pid=273202,fd=5),("nginx",pid=273201,fd=5),("nginx",pid=273200,fd=5),("nginx",pid=273199,fd=5))
tcp   LISTEN 0      4096         0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=2504,fd=3),("systemd",pid=1,fd=190))
tcp   LISTEN 0      511          0.0.0.0:80         0.0.0.0:*    users:(("nginx",pid=273203,fd=6),("nginx",pid=273202,fd=6),("nginx",pid=273201,fd=6),("nginx",pid=273200,fd=6),("nginx",pid=273199,fd=6))
tcp   LISTEN 0      4096      127.0.0.54:53         0.0.0.0:*    users:(("systemd-resolve",pid=604,fd=17))
tcp   LISTEN 0      4096       127.0.0.1:65529      0.0.0.0:*    users:(("monarx-agent",pid=4467,fd=9))
tcp   LISTEN 0      511        127.0.0.1:39359      0.0.0.0:*    users:(("node",pid=404902,fd=43))
tcp   LISTEN 0      4096       127.0.0.1:39709      0.0.0.0:*    users:(("language_server",pid=405025,fd=11))
tcp   LISTEN 0      4096            [::]:8000          [::]:*    users:(("docker-proxy",pid=2053,fd=7))
tcp   LISTEN 0      4096            [::]:9443          [::]:*    users:(("docker-proxy",pid=2069,fd=7))
tcp   LISTEN 0      4096            [::]:22            [::]:*    users:(("sshd",pid=2504,fd=4),("systemd",pid=1,fd=191))
tcp   LISTEN 0      511             [::]:80            [::]:*    users:(("nginx",pid=273203,fd=7),("nginx",pid=273202,fd=7),("nginx",pid=273201,fd=7),("nginx",pid=273200,fd=7),("nginx",pid=273199,fd=7))
NAMES       PORTS                                                                                                STATUS
portainer   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp, 0.0.0.0:9443->9443/tcp, [::]:9443->9443/tcp, 9000/tcp   Up 8 days
```

### Server 3 Verification Command

```bash
ssh server3 "uname -a && cat /etc/os-release && free -h && df -h && ufw status verbose && ss -tulpn && docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'"
```

### Server 3 Verification Output

```
Linux vmi2954037 6.8.0-88-generic #89-Ubuntu SMP PREEMPT_DYNAMIC Sat Oct 11 01:02:46 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
PRETTY_NAME="Ubuntu 24.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.3 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
               total        used        free      shared  buff/cache   available
Mem:            11Gi       3.6Gi       6.4Gi       1.2Mi       2.0Gi       8.1Gi
Swap:             0B          0B          0B
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           1.2G  1.2M  1.2G   1% /run
/dev/sda1       193G   16G  177G   9% /
tmpfs           5.9G     0  5.9G   0% /dev/shm
tmpfs           5.0M     0  5.0M   0% /run/lock
/dev/sda16      881M   64M  756M   8% /boot
/dev/sda15      105M  6.2M   99M   6% /boot/efi
overlay         193G   16G  177G   9% /var/lib/docker/overlay2/8dfc0ef905427b0740caad365b3ce0c698212779380b3dfeecf6123f5f9f964a/merged
tmpfs           1.2G   12K  1.2G   1% /run/user/0
overlay         193G   16G  177G   9% /var/lib/docker/overlay2/38719c3b9d6cfbef6708281a3fa39bb1b07e9e6003db6ffd57d16704ab3870da/merged
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
50001:50002/tcp            ALLOW IN    Anywhere
22/tcp                     ALLOW IN    Anywhere
50001:50002/tcp (v6)       ALLOW IN    Anywhere (v6)
22/tcp (v6)                ALLOW IN    Anywhere (v6)

Netid State  Recv-Q Send-Q               Local Address:Port  Peer Address:PortProcess
udp   UNCONN 0      0                       127.0.0.54:53         0.0.0.0:*    users:(("systemd-resolve",pid=601,fd=16))
udp   UNCONN 0      0                    127.0.0.53%lo:53         0.0.0.0:*    users:(("systemd-resolve",pid=601,fd=14))
udp   UNCONN 0      0                          0.0.0.0:41641      0.0.0.0:*    users:(("tailscaled",pid=80364,fd=18))
udp   UNCONN 0      0                             [::]:41641         [::]:*    users:(("tailscaled",pid=80364,fd=20))
tcp   LISTEN 0      4096                       0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=2110,fd=3),("systemd",pid=1,fd=106))
tcp   LISTEN 0      511                        0.0.0.0:80         0.0.0.0:*    users:(("nginx",pid=79338,fd=5),("nginx",pid=79337,fd=5),("nginx",pid=79336,fd=5),("nginx",pid=79335,fd=5),("nginx",pid=79334,fd=5),("nginx",pid=79333,fd=5),("nginx",pid=79330,fd=5))
tcp   LISTEN 0      4096                       0.0.0.0:50002      0.0.0.0:*    users:(("docker-proxy",pid=804359,fd=7))
tcp   LISTEN 0      4096                       0.0.0.0:50001      0.0.0.0:*    users:(("docker-proxy",pid=65743,fd=7))
tcp   LISTEN 0      4096                     127.0.0.1:36369      0.0.0.0:*    users:(("containerd",pid=61737,fd=9))
tcp   LISTEN 0      4096                    127.0.0.54:53         0.0.0.0:*    users:(("systemd-resolve",pid=601,fd=17))
tcp   LISTEN 0      4096                 100.64.197.32:55057      0.0.0.0:*    users:(("tailscaled",pid=80364,fd=27))
tcp   LISTEN 0      4096                 127.0.0.53%lo:53         0.0.0.0:*    users:(("systemd-resolve",pid=601,fd=15))
tcp   LISTEN 0      4096                          [::]:22            [::]:*    users:(("sshd",pid=2110,fd=4),("systemd",pid=1,fd=107))
tcp   LISTEN 0      511                           [::]:80            [::]:*    users:(("nginx",pid=79338,fd=6),("nginx",pid=79337,fd=6),("nginx",pid=79336,fd=6),("nginx",pid=79335,fd=6),("nginx",pid=79334,fd=6),("nginx",pid=79333,fd=6),("nginx",pid=79330,fd=6))
tcp   LISTEN 0      4096                          [::]:50002         [::]:*    users:(("docker-proxy",pid=804365,fd=7))
tcp   LISTEN 0      4096                          [::]:50001         [::]:*    users:(("docker-proxy",pid=65750,fd=7))
tcp   LISTEN 0      4096   [fd7a:115c:a1e0::5233:c520]:33048         [::]:*    users:(("tailscaled",pid=80364,fd=29))
NAMES          PORTS                                                              STATUS
agent-one-1    22/tcp, 9000-9009/tcp, 0.0.0.0:50002->80/tcp, [::]:50002->80/tcp   Up 55 minutes
agent-zero-1   22/tcp, 9000-9009/tcp, 0.0.0.0:50001->80/tcp, [::]:50001->80/tcp   Up 2 days
```
