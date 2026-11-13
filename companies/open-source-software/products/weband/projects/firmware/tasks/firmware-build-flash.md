---
title: 固件构建与烧录基线
period: day
---
只验证「编译 → 烧录 → 串口」这一条闭环，不实现新功能。输入全部来自本场 brief：目标板名（如 `sf32lb52-nano_n16r16`）、串口设备、应用目录（缺省用 `example/get-started/hello_world/rtt/project`）、SDK 路径。brief 没给板名就停下来问，不要猜 Flash 变体。
开工 30 秒内先建 `digest.md` 骨架，每完成一步立即追加一行：步骤、实测结果、判定。

1. 环境核对：SDK 分支与 commit（应为 `release/v2.5`）、`arm-none-eabi-gcc --version`（应为 14.2.1）、`middleware/bluetooth` 与 `tools/SiliconSchema` 子模块是否已拉取。缺失就按 `/home/whole/data/reawork/refdevice/固件从源码编译成功报告.md` 第 2 节补齐，其中两条踩坑要遵守：不用 `install.sh` 默认的 Python 下载；子模块缺失会导致 `Kconfig not found`。
2. 编译：`source export.sh` 后在应用目录执行 `scons --board=<板名> -j4`。记录 ROM/RAM 用量，并对 `main.elf`、`main.bin`、`ftab.bin` 各算一次 SHA-256。
3. 硬件探测：`lsusb`、`ls /dev/ttyUSB* /dev/ttyACM*`，并确认当前用户在 `dialout` 组。找不到设备就记 blocked 并写明原因，到此为止，不要伪造后续结果。
4. 烧录：先向用户确认端口与板型，再用 `sftool -c SF32LB52 -p <端口> write_flash ...` 烧录。分区与地址取自构建目录里生成的 `sftool_param.json` / `ftab.bin`，不要手写地址。
5. 串口验证：控制台为 `uart1`，波特率 1000000。抓 10 秒日志，判定标准：出现应用 `main.c` 打印的标记（`hello_world` 为 `Hello world!`），启动横幅里的构建日期与 SDK commit 和本次构建一致，回车能得到 `msh />`。`Hello RT-Thread!` 只是镜像里的字符串，不作判据。日志存到 digest 同目录。
   - 人工交互连接（退出按 `Ctrl+]`）：
     ```bash
     python3 -m serial.tools.miniterm --rts 0 --dtr 0 --eol CR /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 1000000
     ```
   - 不要用 `screen`：本板 RTS 接复位，`screen` 会拉有效 RTS 把芯片按在复位里，表现为没有任何输出。脚本抓日志时同样要先释放 RTS 和 DTR（pyserial 里 `rts=False`、`dtr=False`，并在 `open()` 之前设置）。
   - 抓日志或烧录前，先确认没有别的程序占着串口：`fuser -v /dev/ttyUSB0`、`screen -ls`。
6. 收口：digest 末尾写总判定（通过 / 失败 / blocked）、各产物哈希、烧录与串口日志路径。

硬约束：
- 不烧录参考设备原厂 `main.bin`、`dfu.bin` 等镜像，也不改 `ftab` / bootloader 地址。
- 同一个失败最多重试 2 次，之后写出根因并停手。
- 编译产物和日志放在工作目录，不写进 `/home/whole/data/reawork/refdevice`。
