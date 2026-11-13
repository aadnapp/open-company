# Weband 交接记录

最近更新：2026-11-13

## 现状
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
- **M5 OTA / DFU（调研完成，2026-11-13，待用户定 3 个问题后开工）**：
  - V1 用 SiFli SDK 自带的 BLE DFU（`dfu_ctrl` / `ble_dfu`，固件字符串），走 SiFli 串口传输服务（App 里服务 UUID `00000000-0000-0000-6473-5f696c666973`）；App 自己实现 SiFli DFU 协议（START_REQ / PACKET / END_RSP）。V1 另加了一道：`dfu install denied: not armed by authenticated peer`，即 M2 的 `arm_ota` 窗口；OTA 前封口录音（`OTA recorder seal`）。
  - 我们的分区已就位：`dfu_flash_code` 0x720000（384 KB）、`dfu_download_region` 0x780000（1152 KB）。SDK 打包工具有 Python 版（`tools/secureboot/imgtoolv37.py`、`dfu_bin_generate37.py`），Linux 可用。M5 不缺硬件；刷坏了可以随时用 UART + sftool 恢复。
  - 待定：① App 按板型从自带资源里挑 OTA 包，并比较版本号；如果认成参考设备的板型，会把原厂固件推给我们（违反"不刷原厂镜像"）。设备上报什么板型 / 版本，需要定。② 签名密钥：开发阶段用 SDK 默认密钥，量产前换自有密钥（记 TODO）。③ 台架 OTA 工具：自己写 bleak 脚本走同一协议（与 `ble_pull_check.py` 同思路）。
- 新工作项「门控误触发」：独立 worktree；方向是较长窗口内的说话帧比例、或排除骤起骤落的帧；用 `evidence/m3_knock/knocks_concat.wav` 与说话录音 950 / 806 在 `rec_sim` 里量化，再上板复测敲击。
- 然后 M5（OTA / DFU）。
- M3 记的 TODO(weband)：文件名 `.ogg` 与 V1 按小时 `.opus`（App 用 月.日.时 取开始时间）；`file_start` 未发 `start_ts` 等字段；`response` 别名；V1 的 VAD 设置持久化。

## 证据索引
- 每步实测记录：`/home/whole/data/reawork/weband/evidence/digest.md`
- M3：`evidence/m3_night`、`m3_morning`、`m3_speech*`（门控调参）、`m3_xfer`（BLE 传输、fs 修复）、`m3_knock`（敲击测试、夜间分时统计）
- 构建日志：`evidence/build_nano_n16r16.log`、`evidence/build_weband.log`
- 烧录与回读：M0 `flash_hello_world.log` / `flash_readback.txt`；M1 `flash_weband.log` / `flash_readback_weband.txt`
- 串口：`evidence/hello_world_boot_1000000.log`、`evidence/weband_boot_1000000.log`、`evidence/key_monitor.log`
- 出厂备份：`evidence/factory_flash_first4MB.bin`（不入库）

## 卡点 / 风险
- V1 纸面核实已完成（2026-11-10，Weband `docs/hardware-inventory.md` C5，证据 `evidence/nano_sch/`）：模拟麦可直接接 J1-4/5（板上有 2.2 µF 隔直，MIC_BIAS 1.4–2.8 V）；JDI 14 根信号都已引出；**Nano 芯片不带充电，M4 充电部分在 Nano 上 blocked**。
- IMU：V1 固件反汇编确认不访问 LSM6DS3TR-C（0x6A），不对标（证据 `/home/whole/data/reawork/refdevice-v1/analysis/imu_findings.txt` 及同目录脚本）。
- M3 硬件链路实测通过（2026-11-10）：板上烧了 SDK `audprc` 例程（非 hello_world），3037 模拟麦经 MIC_BIAS 供电能拾音，安静 −51 dBFS、出声 −31…−23 dBFS；导出的 8 kHz WAV 用户试听正常（Weband `evidence/digest.md`）。新增 `scripts/serial_capture.py`、`scripts/pcm_stats.py`，修了 `scripts/build.sh` 传参 bug，均未提交。
- 仍未核实：MIC_BIAS 电压值（没有万用表，只间接确认可用）；V1 电源键是否 PA34；Nano 是否引出 SD 接口引脚。
- V1 开源硬件页（2026-11-13，`oshwhub.com/eda_kqtkoxdx/project_bpeoomns`，CERN-OHL-W-2.0，禁止未授权转载）：器件型号已记进 Weband `docs/hardware-inventory.md` 第 2 节与本目录 `AGENTS.md`；设计文件只读不入库。
- BLE 协议逆向基于 V2 固件，M2 用到时要拿 V1 固件字符串（`/home/whole/data/reawork/refdevice-v1/v1_strings.txt`）复核命令与状态串。
- 参考设备长按电源键的时长没有证据；KEY1 按住 10 s 会硬件复位，长按动作必须在此之前触发。
- 参考设备的应用源码私有，M2 起按逆向协议净室重写；无证据的字段标 `TODO(weband)`。
