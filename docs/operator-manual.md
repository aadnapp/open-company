# 人工操作说明书

这份说明书记录需要人来做或人来确认的关键步骤和命令。适用于本机（Ubuntu 20.04，用户 `whole`），最近整理：2026-11-11。

两个工作区：
- **Open Company 配置仓库**：`/home/whole/data/src/open-company`（团队规则、任务、cron 脚本、报告脚本）
- **Weband 固件仓库**：`/home/whole/data/reawork/weband`（板级、构建脚本、实测证据）

产品现状：
- **Weband**：实际在研，固件里程碑 M0、M1 已完成，下一步 M2（BLE 控制协议）。
- **OpenCompare**：只作参考模板，不做实际运营。它的任务文件（盯盘、发版、实测、回帖关单）保留作写法示例，不挂 cron，晚间盘点也不对账。

---

## 1. 什么是自动的，什么要人做

| 事项 | 方式 | 时间 |
|---|---|---|
| 从上游 `munk-sh/open-company` 同步 | **人工**，按 4 节「上游同步（人工）」的 git 步骤 | 按需 |
| 晚间盘点 `daily-patrol` | cron 自动，调用 Kiro CLI | 每天 21:00 |
| 角色 digest + 图形化报告 | cron 自动，纯本地，不联网 | 每小时第 7 分钟 |
| IDE 会话活动记录 | Agent 按 steering 规则记一句话；Stop hook 自动记心跳 | 每轮回复 |
| Weband 构建、烧录、上板验证 | **人工触发**，需要开发板在线 | 按需 |
| 推 tag、发 Release、GitHub 回帖关单、烧录、提交代码 | **必须人确认** | — |

本机网络约 **22:00 断开、09:00 恢复**。需要联网的定时任务只能排在 09:05–21:59 之间。

---

## 2. 每天看什么

```bash
# 图形化报告：数据时间、各角色概览（cron 与 IDE 手动角色）、今日活动、7 天时间线、
# Agent 运行记录、手动任务证据、产品进度、待人处理
xdg-open ~/.local/state/open-company/report/index.html

# 今天的活动日志（IDE 会话记的进展 + Stop hook 心跳），一行一条 JSON
cat ~/.local/state/open-company/activity/$(date +%F).jsonl

# 今天每个角色的 digest
ls ~/.local/state/open-company/digests/$(date +%F)/
cat ~/.local/state/open-company/digests/$(date +%F)/*.md

# 需要人处理的事（Agent 写了 needsOwner: true 的场次）
cat ~/.local/state/open-company/needs-owner.log

# 原始运行日志
ls ~/.local/state/open-company/logs/
```

想马上看最新结果、不等整点：
```bash
cd /home/whole/data/src/open-company/scripts/report && python3 build_digests.py && python3 build_report.py
```

报告不是实时的。页面顶部「数据截至」写了生成时间、下次重建时间和各来源最近更新时间；cron 任务正在跑时，角色卡片显示「运行中」（从 `/proc` 看 `run-task.sh` 进程，不碰任务锁）。

### IDE 会话怎么进报告

IDE 对话本身不进报告，只有写进活动日志的才看得到：
- **一句话进展**：Agent 按 `.kiro/steering/activity-log.md` 调用 `scripts/report/log_activity.py --role <角色> --kind <start|progress|done|blocked|waiting> "<一句话>"`。角色只接受报告里登记过的（`build_report.py` 的 `ROLES` 与 `MANUAL_ROLES`），写错会报错。人也可以手动记一条。
- **会话心跳**：`.kiro/hooks/activity-heartbeat.json`（Stop 触发）每轮回复结束调用 `log_activity.py --heartbeat`，同一工作区 10 分钟内只记一次，只记时间、工作区和 hook 输入的字段名，不记内容。心跳不区分角色。
- 卡片上出现「IDE 会话最近活动…，此后没有记录进展」，说明会话在干活但没记进展，回头补记或提醒 Agent。
- 新增手动角色：在 `build_report.py` 的 `MANUAL_ROLES` 加一行（角色、产品、证据 digest 路径或 `None`），再在 `build_digests.py` 的 `slug()` 给它一个文件名，并同步更新 `activity-log.md` 的角色列表。

产品进度以产品目录下的两份文件为准，**里程碑或等待项变化时要更新**（晚间盘点超过 3 天没更新会列入督办）：
- `companies/open-source-software/products/weband/goal.md`：目标、里程碑、结案条件
- `companies/open-source-software/products/weband/handoff.md`：现状、等待项、下一步、证据索引，顶部写「最近更新」日期

---

## 3. 环境与凭据

### 3.1 已安装的工具（都在用户目录，不需要 sudo）

| 工具 | 位置 | 检查命令 |
|---|---|---|
| Kiro CLI 3.1.0 | `~/.local/bin/kiro-cli` | `kiro-cli --version` |
| GitHub CLI 2.103.3 | `~/.local/bin/gh` | `gh --version` |
| Node 24（guard 脚本需要 ≥18） | `~/.nvm/versions/node/v24.16.0/bin` | 系统自带 `/usr/bin/node` 是 v10，**不能用** |
| pyserial 3.5 | 用户 site-packages | `python3 -c "import serial; print(serial.__version__)"` |
| arm-none-eabi-gcc 14.2.1 | `~/.sifli/tools/arm-none-eabi-gcc/14.2.1` | 由 SiFli SDK 安装 |
| sftool 0.2.5 | `~/.sifli/tools/sftool/0.2.5/sftool` | 由 SiFli SDK 安装 |

### 3.2 凭据文件 `~/.config/open-company/env`

权限必须是 600，**不要提交到任何仓库**。模板：`scripts/cron/env.example`。

| 变量 | 用途 |
|---|---|
| `KIRO_API_KEY` | Kiro CLI 无人值守模式。在 Kiro 账号设置里生成 |
| `GH_TOKEN` | GitHub 身份（当前是 aadnapp 的 fine-grained token，只授权 `aadnapp/open-company`）|
| `GITHUB_REPO` | 值班任务盯的仓库，当前 `aadnapp/open-company` |
| `NODE_DIR` | Node ≥18 所在目录，当前 `/home/whole/.nvm/versions/node/v24.16.0/bin` |

```bash
nano ~/.config/open-company/env && chmod 600 ~/.config/open-company/env

# 验证（不会打印 token 本身）
set -a; . ~/.config/open-company/env; set +a
gh api user --jq .login                           # 应输出 aadnapp
kiro-cli chat --no-interactive --trust-tools= "只回复 ok"   # 应输出 ok
```

token 过期（GH_TOKEN 设了 90 天）或换账号时，只改这个文件，不用动脚本。

---

## 4. 定时任务（cron）

```bash
crontab -l                                         # 查看当前排班
crontab /home/whole/data/src/open-company/scripts/cron/crontab.example   # 按模板整体替换
crontab -e                                         # 手动编辑，删行即停用
```

注意：`crontab <文件>` 会**整体替换**当前用户的 crontab。替换前先 `crontab -l` 确认里面没有别的条目，必要时先备份：`crontab -l > ~/crontab.bak`。

手动跑一次某个任务（和 cron 走同一条路径）：
```bash
/home/whole/data/src/open-company/scripts/cron/run-task.sh daily-patrol; echo "exit=$?"
```
`run-task.sh` 的退出码：0 正常；64 任务名不对；78 缺 `KIRO_API_KEY`；127 缺命令（`kiro-cli`、`gh`，或 Node 版本太低）；2 guard 自身出错。

每场的输出：
- 运行日志：`~/.local/state/open-company/logs/<任务>-<日期>.log`
- 每场 digest 与 Agent 输出：`~/.local/state/open-company/runs/<任务>/<时间戳>/{digest.md,agent.log}`

### 上游同步（人工）

本仓库有两个远端：`origin` 是上游 `munk-sh/open-company`（只拉不推），`fork` 是我们自己的 `aadnapp/open-company`（本地 `main` 跟踪 `fork/main`）。不自动同步，需要时按下面步骤手动做：

```bash
cd /home/whole/data/src/open-company
git status --short                     # 1. 工作区必须干净，有改动先提交
git fetch origin                       # 2. 拉上游；网络时好时坏，失败就过一会儿再试
git log --oneline HEAD..origin/main    # 3. 看上游有哪些新提交；没有输出就不用同步
git diff --stat HEAD...origin/main     #    看改了哪些文件，留意 AGENTS.md 和 tasks/*.md
git merge --no-ff origin/main          # 4. 合并；有冲突时解决后 git add <文件> && git commit，放弃用 git merge --abort
```

5. 重新生成 `catalog.json`，有变化就单独提交（否则仓库的 CI 检查会失败）：
```bash
PATH=/home/whole/.nvm/versions/node/v24.16.0/bin:$PATH node scripts/build-catalog.mjs
git diff --stat catalog.json           # 有输出才需要下一行
git commit -m "chore: rebuild catalog.json after upstream merge" catalog.json
```

6. 检查 steering 引用的源文件是否都还在（有 `MISSING` 输出，说明上游改名或删除了被引用的文件，要同步改 `.kiro/steering/` 里对应的 `#[[file:...]]`）：
```bash
for f in $(grep -ho '#\[\[file:[^]]*\]\]' .kiro/steering/*.md | sed 's/#\[\[file://;s/\]\]//' | sort -u); do [ -f "$f" ] || echo "MISSING $f"; done
```

7. 推送到自己的 fork：
```bash
git push fork main
```

### 无人值守场次的安全边界
cron 场次里 Agent 是用 `--trust-all-tools --trust-workspace` 启动的，工具调用不再逐个确认。挡住推 tag、发版、删文件这类操作的，只有 prompt 里的规则，没有技术拦截。要收紧，在 env 里设 `KIRO_TRUST_FLAGS` 只放行指定工具。

---

## 5. 在 Kiro IDE 里手动触发任务

在对话里输入任务名，并在同一条消息里写本场 brief：

| 任务 | 触发 | brief 要给什么 |
|---|---|---|
| 晚间盘点 | `#task-daily-patrol` | 无 |
| Weband 构建烧录基线 | `#task-firmware-build-flash` | 板名、串口、应用目录 |
| Weband 功能移植 | `#task-firmware-port` | 里程碑编号、板名、要实现的行为 |

OpenCompare 的 `#task-*` 只作参考模板，不要实际触发。

---

## 6. Weband 固件

### 6.1 开发板

SF32LB52-DevKit-Nano-R16N16（芯片 SF32LB52JUD6，16 MB NOR + 16 MB PSRAM），板级名 `sf32lb52-weband`。USB-C 接本机，枚举为 CH340 串口 `/dev/ttyUSB0`。

板上位置（正面，USB-C 朝自己）：
- **KEY1**：USB-C 左边的按键，PA34，按下为高。**按住 10 秒会硬件复位**。
- **KEY2**：USB-C 右边的按键，PA33，按下为高。
- **两个 LED**：右下角，丝印 `PA31`（外侧）、`PA32`（内侧），**低电平点亮**。
- 板上**没有独立复位键**。复位用 shell 命令 `reboot`，或切换一次串口的 RTS。

### 6.2 构建

```bash
cd /home/whole/data/reawork/weband
scripts/build.sh                                   # 默认编 hello_world，板 sf32lb52-weband
scripts/build.sh <工程目录> sf32lb52-weband          # 编其它 SCons 工程
```
`build.sh` 会检查 SDK 是否在固定 commit `87d5700a`，不在就拒绝编译。产物在 `<工程目录>/build_sf32lb52-weband_hcpu/`。

### 6.3 烧录（会改写板子 Flash，先确认）

1. 确认串口没被占用：
   ```bash
   fuser -v /dev/ttyUSB0          # 没有输出才算空闲
   screen -ls                     # 不应有 screen 会话
   ```
2. 烧录。地址取自构建目录的 `sftool_param.json`，**不要手写别的地址**：
   ```bash
   cd <工程目录>/build_sf32lb52-weband_hcpu
   cat sftool_param.json          # 核对地址
   ~/.sifli/tools/sftool/0.2.5/sftool -c SF32LB52 -p /dev/ttyUSB0 write_flash --verify \
     bootloader/output/bootloader.bin@0x12010000 output/main.bin@0x12020000 ftab.bin@0x12000000
   ```
3. 回读校验（逐个区读回来比对 SHA-256，三行都应是 MATCH）：
   ```bash
   S=~/.sifli/tools/sftool/0.2.5/sftool
   for spec in "bootloader/output/bootloader.bin 0x12010000" "output/main.bin 0x12020000" "ftab.bin 0x12000000"; do
     set -- $spec; n=$(stat -c %s $1); o=/tmp/rb_$(basename $1)
     $S -c SF32LB52 -p /dev/ttyUSB0 -q read_flash $o@$2:$(printf '0x%x' $n) >/dev/null 2>&1
     [ "$(sha256sum < $1)" = "$(sha256sum < $o)" ] && echo "$2 MATCH" || echo "$2 MISMATCH"; rm -f $o
   done
   ```
4. 把烧录日志、哈希和回读结果追加到 `evidence/digest.md`。

禁止事项：不烧 refdevice 原厂镜像（`main.bin`、`dfu.bin`、`ftab.bin`、`bootloader.bin`）；不改 `ftab` 和 bootloader 地址。

### 6.4 串口

```bash
python3 -m serial.tools.miniterm --rts 0 --dtr 0 --eol CR /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 1000000
```
- 按回车出现 `msh />`；`help` 列命令；`version` 看版本；`reboot` 重启看启动日志。
- 退出按 `Ctrl+]`。
- **不要用 `screen`**：本板 RTS 接复位，`screen` 会把芯片一直按在复位里，表现为回车没反应。直接关终端窗口也不会退出 `screen`，它会在后台继续占着串口：
  ```bash
  screen -ls                       # 查看
  screen -S <会话id> -X quit        # 退出
  ```
- 用 `--eol CR`，不要用 `CRLF`（否则一次回车被当成两次，出现 `msh />msh />`）。
- 命令一条一条打，不要一次粘贴多行，否则会丢字符。
- 同一时间只能有一个程序占用串口，**烧录前先退出 miniterm**。

### 6.5 引脚手动测试（shell 里一条一条打）

```
pin mux 31 0          # PA31 切成 GPIO
pin mode 31 0         # 设为输出
pin write 31 0        # 写 0：LED 亮
pin write 31 1        # 写 1：LED 灭
pin status 31         # 查看当前功能、电平、模式

pin mux 34 0          # KEY1
pin read 34           # 按住 KEY1 时为 1，松开为 0
```

### 6.6 还原出厂固件（未实测，只在必要时用）

出厂固件的前 4 MB 已备份（出厂内容只占 `0x12000000–0x12090000`，这份备份完整覆盖）：
```
/home/whole/data/reawork/weband/evidence/factory_flash_first4MB.bin
SHA-256 0343fa709bf26bbeb1b1046803eb1f9236d41b72746ee0a49ada49d762913c01
```
```bash
cd /home/whole/data/reawork/weband/evidence
sha256sum factory_flash_first4MB.bin                # 先核对哈希
~/.sifli/tools/sftool/0.2.5/sftool -c SF32LB52 -p /dev/ttyUSB0 write_flash --verify factory_flash_first4MB.bin@0x12000000
```
这条命令没有实际执行过。写入 4 MB 需要几分钟；写完用 miniterm 确认出现出厂横幅 `SF32LB52-Nano V1.1.0`。

### 6.7 提交与分支

- 仓库 `/home/whole/data/reawork/weband`，分支 `main`，首次提交 `a6f1c46`（2026-11-10）。
- 远端 `origin` = `git@github.com:aadnapp/weband.git`（私有，2026-11-10 已推送 `main`）。之后推送前先测连通：
  ```bash
  ssh -T git@github.com                         # 正常会提示 "Hi aadnapp! ..."
  git -C /home/whole/data/reawork/weband ls-remote origin
  git -C /home/whole/data/reawork/weband push -u origin main
  ```
  本机所在网络会切断到 GitHub 的 SSH 握手（时好时坏：2026-11-10 上午多次 `Connection reset by peer`，稍后恢复），`https://github.com` 也连不上，只有 `api.github.com` 可用。这时换网络或代理再推；或者打包到别的机器推送，提交与作者原样保留：
  ```bash
  git -C /home/whole/data/reawork/weband bundle create /tmp/weband.bundle main
  git bundle verify /tmp/weband.bundle
  # 拷到能上 GitHub 的机器后：
  git clone /path/to/weband.bundle weband && cd weband
  git remote set-url origin git@github.com:aadnapp/weband.git && git push -u origin main
  ```
- 不入库：`sifli-sdk/`、构建输出、`evidence/*.bin`、`docs/img/`、`.vscode/`（见 `.gitignore`）。
- M2 起每个研发工作项在独立 worktree 里做，完成后再合回 `main`：
  ```bash
  git -C /home/whole/data/reawork/weband worktree add .worktrees/<名字> -b <分支名> main
  ```
- 推到远端前：把 `sifli-sdk` 子模块的 URL 改回官方地址（当前指向本地 `.git/modules`）。

### 6.8 BLE 联调用的 USB 蓝牙适配器（UGREEN，需要 sudo）

本机用 UGREEN 适配器（USB `2b89:8761`，芯片 RTL8761B）当 BLE central。Ubuntu 20.04 的 5.15 内核**不认这个 ID**，不打补丁时驱动不给芯片下载固件，芯片停在 ROM，扫不到任何设备。2026-11-11 做了两件事让它可用：

1. **补丁版 btusb**：`~/src/btusb-2b89/`，源码取自 Ubuntu 内核 git 标签 `Ubuntu-hwe-5.15-5.15.0-139.149_20.04.1`（未打补丁时 srcversion 与原装模块一致），只在 `blacklist_table` 加一行 `2b89:8761 → BTUSB_REALTEK`（`ugreen-2b89-8761.patch`）。装在 `/lib/modules/5.15.0-139-generic/updates/btusb.ko`。
2. **固件**：内核要的是 `rtl8761bu_fw.bin` / `rtl8761bu_config.bin`，本机 linux-firmware 包里没有，从 linux-firmware 上游下载后手工放进 `/lib/firmware/rtl_bt/`。

检查是否正常：
```bash
modinfo -F srcversion btusb                 # 15CF02527CA99AE214C3561 = 补丁版
sudo dmesg | grep -i "RTL" | tail -4         # 应有 loading rtl8761bu_fw.bin 和 fw version 0x...
hciconfig hci0 version                       # Subversion 不是 0x8761 就说明固件已加载
```

**内核升级后适配器会失效**（新内核用回原版 btusb）。用新内核的源码重做：
```bash
cd ~/src/btusb-2b89
K=$(uname -r)                                 # 例如 5.15.0-140-generic
# 标签名按 /proc/version_signature 写，形如 Ubuntu-hwe-5.15-5.15.0-140.150_20.04.1
T="Ubuntu-hwe-5.15-<版本>_20.04.1"
B="https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/focal/plain/drivers/bluetooth"
for f in btusb.c btintel.h btbcm.h btrtl.h; do curl -fsS -o $f "$B/$f?h=$T"; done
make -C /lib/modules/$K/build M=$PWD modules && modinfo -F srcversion ./btusb.ko   # 先确认与 modinfo -F srcversion btusb 相同
patch -p0 btusb.c < ugreen-2b89-8761.patch && make -C /lib/modules/$K/build M=$PWD modules
sudo install -D -m 644 btusb.ko /lib/modules/$K/updates/btusb.ko && sudo depmod -a
sudo modprobe -r btusb && sudo modprobe btusb
```

撤回（恢复原版驱动，固件文件留着无害）：
```bash
sudo rm /lib/modules/$(uname -r)/updates/btusb.ko && sudo depmod -a
sudo modprobe -r btusb && sudo modprobe btusb
```

---

## 7. 常见故障

| 现象 | 原因 | 处理 |
|---|---|---|
| 串口回车没反应 | 用了 `screen`，RTS 把芯片按在复位里 | 改用 6.4 的 miniterm 命令；`screen -ls` 清掉残留会话 |
| `Device or resource busy` | 串口被别的程序占用 | `fuser -v /dev/ttyUSB0` 找到进程，先正常退出它 |
| 出现 `msh />msh />` | 用了 `--eol CRLF` | 改成 `--eol CR` |
| 命令被截断、`command not found` | 一次粘贴了多行 | 一条一条打 |
| guard 返回 1 但其实没检查 | 系统 node v10 跑不了 ES module，或没装 `gh` | 确认 env 里 `NODE_DIR` 正确；`run-task.sh` 会先检查，不满足时以 127 退出 |
| 夜间日志全是 `gh ETIMEDOUT` | 本机 22:00–09:00 断网 | 需要联网的任务不要排在这个时段 |
| `KIRO_API_KEY not set`（退出码 78） | env 文件没填或没权限读 | 见 3.2 |
| 烧录 `sftool` 连不上 | 串口被占用，或板子没接好 | 先查 `fuser`；重新插拔 USB-C 后看 `ls /dev/ttyUSB*` |
| 晚间盘点把产品标成 blocked | `goal.md` / `handoff.md` 缺失或太久没更新 | 更新产品目录下这两份文件 |
