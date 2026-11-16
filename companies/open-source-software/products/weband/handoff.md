# Weband 交接记录

最近更新：2026-11-16（V1 实物整片 NOR 只读备份）

## 现状
- **V1 实物整片备份（2026-11-16，上 Weband 固件分步方案第 1 步）**：V1 经 USB-C 转 TTL 转接板接 `/dev/ttyACM0`，用 `sftool read_flash` 只读读出 16 MB NOR，SHA-256 `db02fe1a…84acb917`，存仓库外 `/home/whole/data/reawork/refdevice-v1/flash_backup/v1_nor_full_16MB.bin`（不入库）。bootloader 与手头原厂镜像一致，main、dfu 不一致（V1 上是别的版本），还原只能用这份备份。读完 V1 自动重启，运行正常。记录在 Weband `evidence/digest.md`（未提交）。
  - 第 2 步已完成（只编译）：板级 `sf32lb52-weband-v1` 在 Weband worktree `.worktrees/board-weband-v1`，分支 `board-weband-v1` 提交 `7d63b0d`，未合入 `main`。525、8 MB PSRAM `MPI1_MODE_3`、片内充电、引脚按 V1 网表核对；电池保护（自有定义）：4200/4350 mV、120 mA，开机 <3500 mV、运行中 <3400 mV 无充电器即休眠。PSRAM、VBAT 读数、充电、休眠都未上板验证。
  - 第 3、4 步已完成（2026-11-16，用户逐步确认后烧录）：先只写探测固件 main.bin（方案 B），V1 原 bootloader 能引导，PSRAM 8 MB 0 错，PA34 电源键可读，10 s 强制复位通过；再 4 个镜像全刷完整 Weband（方案 A，提交 `74f3566` 构建）。V1 上实测：开机、V1 模拟麦录音、BLE 广播 `Weband-44D1`、按键配对 → 鉴权 → 拉 16 段录音 69/69 → 解绑回开放模式、单击录灵感和 60 s 超时关闭，全部通过。证据在 Weband `evidence/digest.md` 与 `evidence/0026_v1_ble/`、`evidence/v1_*.log`（未提交）。
  - V1 现在跑的是 Weband，原厂固件可用 `refdevice-v1/flash_backup/v1_nor_full_16MB.bin` 整片写回。
  - 待用户决定：分支 `board-weband-v1` 是否合入 `main`；600 ms–6 s 的按压是否补日志；录音改走 V1 的 SD NAND（现在仍写 NOR `fs_region`）；拔掉 Type-C 充电器测电池保护和续航。
  - 接法（2026-11-16 用户确认）：转接板接 V1 的 3 针调试口（网表 U7：GND / TXD / RXD，不供电）；Type-C 另插充电器在充电。V1 的 Type-C D+/D- 和 3 针口并在同一对串口线上（A6/B6=TXD，A7/B7=RXD），CC 各有下拉电阻。整片备份就是在这个接法下读成功的，说明这个充电器不干扰串口，换充电器前要重新确认。
  - 续航和电池保护测试暂缓：Type-C 充电器插着，要拔掉才能测。
- **硬件工程去屏幕（2026-11-16）**：新建本地仓库 `/home/whole/data/reawork/weband_hw`（独立 git，未设远端），`weband.eprj2` 是参考设备 V1 开源工程的副本，用 `lceda-pro` 命令行修改：删 LCD 页和 12 个器件，U1 的 15 个 LCD 引脚改 No Connect，PCB 导入变更并清掉屏幕走线、残线，重建铺铜。原理图 DRC 仍是原有 16 条 warn；PCB DRC 通过，飞线 0 条。存储（SD NAND、NOR）未动，**未在 dev nano 上调试**。证据：`weband_hw/evidence/`（`25_netlist_diff.txt`、`30_connectivity_check.txt`、`32_pcb_final.json`），提交 `95fbdfb`（历史已重写，见下）。
  - 红线处理（2026-11-16 用户决定）：① `weband_hw` **只在本地保存，不设远端、不推送**，因为工程派生自 V1 开源设计，授权未确认；② README、提交说明、`evidence/03_src_info.json` 改为中性写法，本地历史已用 `filter-branch` 重写，现 `main` = `5ba782a`。工程文件内部仍带参考设备名，属于设计内容本身，仓库不外传，所以不改。重写前的备份分支 `backup-before-neutral` 和 `refs/original` 已按用户确认删除并 gc，旧提交已不可达。
- **M4 电源键部分：已完成（2026-11-13）**，已快进合入 Weband `main` 并推送（`origin/main` = `f1de797`），worktree 与分支已清理，不入库的镜像与升级包已移到主仓 `evidence/0021_m4_power_key/`。板上跑 build 3（BLE OTA 装上），开放模式。证据：Weband `evidence/digest.md` 2026-11-13 M4 一节、`evidence/0021_m4_power_key/`。
  - 单击灵感（默认 60 s，`idea_toggle` / `idea_config` 按 V1）、双击重新配对（清令牌和 BLE 绑定后重启，录灵感时延后）、长按 6 s 重启、延后遇长按先解绑，都已实测。
  - 实测中修了两处：延后的重新配对会被长按重启丢掉；全新配对后第一次连接 App 层配对被拒（SDK 不发加密事件）。
  - 台架脚本连接改为 `connect_live`（老 BlueZ 扫描停止即删未绑定设备）。
  - V1 原理图：电源键 PA34 高有效（SKRTLAE010）；无蜂鸣器；SD NAND 走 SPI，接 PA24/25/28/29，Nano J1 有这四个脚。
  - 无屏配对已定（2026-11-13）：**真实用户通过按键完成配对**（按 V1 的 `button_confirm`）。固件侧已真机通过（2026-11-14）：用户单击 KEY1 约 39 s 后配对成功并拿到令牌；不按则 60 s 后回 `expired`。已合入 Weband `main` 并推送（`55a23f5`），worktree 已清理。原版 App 不发这种方式，需要我们自己的 App 配合。
  - 待办（2026-11-13 用户提出）：**用敲击或"敲击 + 划动"组成的莫斯码完成配对**；识别用什么传感器、码怎么生成和比对都待定，见 `goal.md`。
- **硬件范围（2026-11-13）**：对标 V1，但 **Weband 不要屏幕**。V1 器件按其开源硬件页更新：SF32LB525UC6、128 MB SD NAND 存录音、16 MB SPI NOR、502525 电池、IMU 在板但固件不用。M4 改为只做电源（电源键 + 充电）。
- **M3 录音已完成（2026-11-13）**：已快进合入 Weband `main` 并推送（`origin/main` = `97ec141`），worktree 与分支已清理；工作树外的录音文件（`.ogg` / `.wav` / `fs_region.img`，不入库）已移到主仓 `evidence/` 下。板上跑 `main.bin` `5c0c03cf…0fd9`，处于开放模式（未配对）。
  - 录音：WebRTC VAD 门控（余量 8 dB、触发 6 帧）+ Opus SILK 16 kHz 24 kbit/s，60 s 一段写 `/weband/rec/NNNNNN.ogg`。
  - 存储：已用超过 2/3 开始裁剪（用户定），先删已传到手机的（`ACKED.txt`），再删最旧的，删到剩余 1/3 + 256 KB；5 分钟 fsync（用户定）；开机删空文件。实测：先删 9 个已 ACK、再删 3 个最旧，丢帧 0。
  - BLE 传录音：按原版 App 1.3.1 的 `ready` / `ack` + MBF1 帧实现。台架脚本 `scripts/ble_pull_check.py` 实测：基本拉取、丢块重传、断线续传都通过，206 个积压文件一次拉完 829/829。
  - 鉴权改为与原版 App 一致：`{"type":"auth","mac"}`，key 为令牌 hex 解码的 16 字节（M2 原实现与 App 不兼容）。
  - 上板修过的问题：main 线程栈 2 KB 溢出（改 8 KB，开机裁剪移到录音线程）；这次崩溃把 fs_region 的 rec 目录扇区擦成 0xFF，已在主机上重建元数据写回（旧测试录音丢失，有用的早已取回）。
  - 敲击测试未达标：敲击 1 分钟开 4 段；拉长触发到 12 帧仍有 2 段。用户决定 M3 先收尾，单独立项。夜里 22:00–07:00 无人时只开 3 段。
- **对标改为参考设备 V1 圆屏**（2026-11-10 用户决定）。依据：V1 固件 `1.15.35-v1-round-serial`（板级 `sf32lb52-refboard-v1`）字符串里有 30 处 audcodec/audprc、0 处 PDM，显示为 `jdi387a`，充电走片内 PMU；V2 固件 `2.15.12` 则是 22 处 PDM、0 处 audcodec、JD7601、LGS4056。V1 原理图（`/home/whole/share/mic_imu.webp`）的模拟麦 `MIC_BIAS`/`MIC_ADC` 与 V1 固件一致。此前文档里的"PDM 麦"只适用于 V2。
  - 已更新：`AGENTS.md`、`goal.md`、Weband 仓库 `docs/hardware-inventory.md`（第 2 节改为 V1 外设，V2 移到 2b，待核实项 C5）、`firmware-port.md` 资料入口。Weband 仓库的改动尚未提交。
  - 原 V2 设计文档（`/home/whole/data/reawork/refdevice-files/v2-design.md`）是 V2 设计，外设部分不再适用。
- M0 已完成（2026-11-09）：hello_world 在 Nano 上编译、烧录、回读一致、串口启动正常。
- M1 已完成（2026-11-10）：
  - 树外板级 `boards/sf32lb52-weband`，编译通过；除板名与 LED 极性外与 SDK 的 Nano 板等价。
  - 分区表核对：16 MB NOR 原样放下参考设备的分区布局，不重排。
  - 外设清点 `docs/hardware-inventory.md`；真机核对：LED（PA31/PA32）低电平点亮，KEY1=PA34、KEY2=PA33 按下为高。
  - weband 版已烧录上板：三区回读一致，串口启动、`Hello world!`、`msh />` 正常。

- 首次提交已完成（2026-11-10）：`main` @ `a6f1c46`（两个提交已合并为一个），38 个文件；SDK、Flash 镜像、板图不入库。
- 远端：`origin` = `git@github.com:aadnapp/weband.git`（私有）。2026-11-10 已推送 `main`，远端与本地同为 `a6f1c46`。

- M2 开工（2026-11-11）：worktree `/home/whole/data/reawork/weband/.worktrees/m2-ble-protocol`，分支 `m2-ble-protocol`（基于 main `606e0fa`）。提交 `5998086`：把我们早先示例的协议核心（mb_proto / mb_frame / mb_hmac）和主机单测移到 `app/`，`make -C app/test/host check` 72/72 通过。GATT / 存储 / 平台胶水（原 b2074d76）尚未移植。
- **M2 已完成（2026-11-11）**：已快进合入 Weband `main` 并推送（`37fcb56`），worktree 与分支已清理。协议按 V1 对齐（只核对 M2 命令），主机单测 75/75；真机 BLE 联调 `scripts/ble_m2_check.py --reboot --unpair` 17/17：pair → auth → ok、未认证 arm_ota 回 auth_required、认证后 armed、令牌跨复位有效、远程 unpair。修了两处上板问题：TRNG 未播种导致 rng_error；BlueZ 的 Just Works 需要 agent 授权（脚本自带 D-Bus agent）。（板上现在跑的是 M3 固件，见上。）
- 联调用 UGREEN 蓝牙适配器（RTL8761B），靠补丁版 btusb + 手工放的 rtl8761bu 固件才能用，见操作手册 6.8；换内核要重做。
- 两仓 2026-11-11 均已推送：Weband `origin/main` = `37fcb56`；open-company `fork/main`。

## 等待项（等人）
1. 采购 P1 外设（见 `goal.md`），不阻塞 P0。按 V1、不要屏幕（2026-11-13）：麦已有（3037 模拟麦）；不再需要屏。录音存储要 SD NAND / SD 卡模块（或按 V1 开源设计打板），充电要锂电版芯片的板子 + 锂电池（V1 为 502525），是否购买或打板待用户决定。不再需要 PDM 麦、JD7601、LGS4056、JDI 屏。
4. 用户决定：无屏后 `MBWP` 壁纸帧在线协议上怎么处理（照收丢弃，或回不支持）。
2. 用户已定（2026-11-13）：下一步做 M5（OTA / DFU）。调研结论与待定项见下一步。
3. 用户决定：录音存储掉电安全方案（NOR 上 FAT 改目录时掉电丢整个目录）是否排期。

## 下一步
- 待办（2026-11-16 用户提出）：**Weband 没有蜂鸣器**，用户提示只能靠 LED 等方式，各状态的闪法待定，见 `goal.md`。
- **M5 OTA / DFU：已完成（2026-11-13）**，已快进合入 Weband `main` 并推送（`origin/main` = `4ccce97`），worktree 与分支已清理；不入库的镜像、升级包与拉回的录音已移到主仓 `evidence/0020_m5_ota/`。板上跑最终版 `main.bin` `d706c012…`（构建 `Nov 13 2026 14:00:44`，经 BLE OTA 装上），开放模式。证据：Weband `evidence/digest.md` 2026-11-13 M5 一节、`evidence/0020_m5_ota/`。
  - 结果：不开窗被拒 5/5；A→B 11/11；断线续传 9/9；C→最终版 8/8（46 s，11.2 KB/s）；OTA 后回读主程序区与最终版逐字节一致；开窗过期被拒 6/6；OTA 后拉录音 17/17；配对跨三次 OTA 保持。
  - 记的 TODO：不上报 `hw` / `fw_version`；离线包不签名，只靠 arm_ota 闸门；板上 rt_tick 慢约 1%；安装器有两条告警（结果正常，未深究）；安装中掉电续装未实测。
- （以下为开工前的调研记录）
  - V1 用 SiFli SDK 自带的 BLE DFU（`dfu_ctrl` / `ble_dfu`，固件字符串），走 SiFli 串口传输服务（App 里服务 UUID `00000000-0000-0000-6473-5f696c666973`）；App 自己实现 SiFli DFU 协议（START_REQ / PACKET / END_RSP）。V1 另加了一道：`dfu install denied: not armed by authenticated peer`，即 M2 的 `arm_ota` 窗口；OTA 前封口录音（`OTA recorder seal`）。
  - 我们的分区已就位：`dfu_flash_code` 0x720000（384 KB）、`dfu_download_region` 0x780000（1152 KB）。SDK 打包工具有 Python 版（`tools/secureboot/imgtoolv37.py`、`dfu_bin_generate37.py`），Linux 可用。M5 不缺硬件；刷坏了可以随时用 UART + sftool 恢复。
  - 待定：① App 按板型从自带资源里挑 OTA 包，并比较版本号；如果认成参考设备的板型，会把原厂固件推给我们（违反"不刷原厂镜像"）。设备上报什么板型 / 版本，需要定。② 签名密钥：开发阶段用 SDK 默认密钥，量产前换自有密钥（记 TODO）。③ 台架 OTA 工具：自己写 bleak 脚本走同一协议（与 `ble_pull_check.py` 同思路）。
- 新工作项「门控误触发」：独立 worktree；方向是较长窗口内的说话帧比例、或排除骤起骤落的帧；用 `evidence/0019_m3_knock/knocks_concat.wav` 与说话录音 950 / 806 在 `rec_sim` 里量化，再上板复测敲击。
- 然后 M5（OTA / DFU）。
- M3 记的 TODO(weband)：文件名 `.ogg` 与 V1 按小时 `.opus`（App 用 月.日.时 取开始时间）；`file_start` 未发 `start_ts` 等字段；`response` 别名；V1 的 VAD 设置持久化。

## 证据索引
- 每步实测记录：`/home/whole/data/reawork/weband/evidence/digest.md`
- M3：`evidence/0012_m3_night`、`m3_morning`、`m3_speech*`（门控调参）、`m3_xfer`（BLE 传输、fs 修复）、`m3_knock`（敲击测试、夜间分时统计）
- 构建日志：`evidence/0002_build_baseline/build_nano_n16r16.log`、`evidence/0007_m1_weband_board/build_weband.log`
- 烧录与回读：M0 `0005_m0_hello_world/flash_hello_world.log` / `0005_m0_hello_world/flash_readback.txt`；M1 `0007_m1_weband_board/flash_weband.log` / `0007_m1_weband_board/flash_readback_weband.txt`
- 串口：`evidence/0005_m0_hello_world/hello_world_boot_1000000.log`、`evidence/0007_m1_weband_board/weband_boot_1000000.log`、`evidence/0006_led_key_test/key_monitor.log`
- 出厂备份：`evidence/0003_factory_backup/factory_flash_first4MB.bin`（不入库）

## 卡点 / 风险
- V1 纸面核实已完成（2026-11-10，Weband `docs/hardware-inventory.md` C5，证据 `evidence/0008_nano_sch/`）：模拟麦可直接接 J1-4/5（板上有 2.2 µF 隔直，MIC_BIAS 1.4–2.8 V）；JDI 14 根信号都已引出；**Nano 芯片不带充电，M4 充电部分在 Nano 上 blocked**。
- IMU：V1 固件反汇编确认不访问 LSM6DS3TR-C（0x6A），不对标（证据 `/home/whole/data/reawork/refdevice-v1/analysis/imu_findings.txt` 及同目录脚本）。
- M3 硬件链路实测通过（2026-11-10）：板上烧了 SDK `audprc` 例程（非 hello_world），3037 模拟麦经 MIC_BIAS 供电能拾音，安静 −51 dBFS、出声 −31…−23 dBFS；导出的 8 kHz WAV 用户试听正常（Weband `evidence/digest.md`）。新增 `scripts/serial_capture.py`、`scripts/pcm_stats.py`，修了 `scripts/build.sh` 传参 bug，均未提交。
- 仍未核实：MIC_BIAS 电压值（没有万用表，只间接确认可用）；V1 电源键是否 PA34；Nano 是否引出 SD 接口引脚。
- V1 开源硬件页（2026-11-13，`oshwhub.com/eda_kqtkoxdx/project_bpeoomns`，CERN-OHL-W-2.0，禁止未授权转载）：器件型号已记进 Weband `docs/hardware-inventory.md` 第 2 节与本目录 `AGENTS.md`；设计文件只读不入库。
- BLE 协议逆向基于 V2 固件，M2 用到时要拿 V1 固件字符串（`/home/whole/data/reawork/refdevice-v1/v1_strings.txt`）复核命令与状态串。
- 参考设备长按电源键的时长没有证据；KEY1 按住 10 s 会硬件复位，长按动作必须在此之前触发。
- 参考设备的应用源码私有，M2 起按逆向协议净室重写；无证据的字段标 `TODO(weband)`。
