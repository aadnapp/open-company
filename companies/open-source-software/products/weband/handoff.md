# Weband 交接记录

最近更新：2026-11-10

## 现状
- **对标改为 refdevice V1 圆屏**（2026-11-10 用户决定）。依据：V1 固件 `1.15.35-v1-round-serial`（板级 `sf32lb52-refboard-v1`）字符串里有 30 处 audcodec/audprc、0 处 PDM，显示为 `jdi387a`，充电走片内 PMU；V2 固件 `2.15.12` 则是 22 处 PDM、0 处 audcodec、JD7601、LGS4056。V1 原理图（`/home/whole/share/mic_imu.webp`）的模拟麦 `MIC_BIAS`/`MIC_ADC` 与 V1 固件一致。此前文档里的"PDM 麦"只适用于 V2。
  - 已更新：`AGENTS.md`、`goal.md`、Weband 仓库 `docs/hardware-inventory.md`（第 2 节改为 V1 外设，V2 移到 2b，待核实项 C5）、`firmware-port.md` 资料入口。Weband 仓库的改动尚未提交。
  - 原 `refboard-v2/design.md` 是 V2 设计，外设部分不再适用。
- M0 已完成（2026-11-09）：hello_world 在 Nano 上编译、烧录、回读一致、串口启动正常。
- M1 已完成（2026-11-10）：
  - 树外板级 `boards/sf32lb52-weband`，编译通过；除板名与 LED 极性外与 SDK 的 Nano 板等价。
  - 分区表核对：16 MB NOR 原样放下 refdevice 布局，不重排。
  - 外设清点 `docs/hardware-inventory.md`；真机核对：LED（PA31/PA32）低电平点亮，KEY1=PA34、KEY2=PA33 按下为高。
  - weband 版已烧录上板：三区回读一致，串口启动、`Hello world!`、`msh />` 正常。
- 板上当前运行的是 `sf32lb52-weband` 版 hello_world。

- 首次提交已完成（2026-11-10）：`main` @ `a6f1c46`（两个提交已合并为一个），38 个文件；SDK、Flash 镜像、板图不入库。
- 远端：`origin` = `git@github.com:aadnapp/weband.git`（私有）。2026-11-10 已推送 `main`，远端与本地同为 `a6f1c46`。

- M2 开工（2026-11-11）：worktree `/home/whole/data/reawork/weband/.worktrees/m2-ble-protocol`，分支 `m2-ble-protocol`（基于 main `bb4ca8d`）。提交 `00efbb7`：把我们早先 refboard 示例的协议核心（mb_proto / mb_frame / mb_hmac）和主机单测移到 `app/`，`make -C app/test/host check` 72/72 通过。GATT / 存储 / 平台胶水（原 b2074d76）尚未移植。
- **M2 已完成（2026-11-11）**：已快进合入 Weband `main` 并推送（`dba20aa`），worktree 与分支已清理。协议按 V1 对齐（只核对 M2 命令），主机单测 75/75；真机 BLE 联调 `scripts/ble_m2_check.py --reboot --unpair` 17/17：pair → auth → ok、未认证 arm_ota 回 auth_required、认证后 armed、令牌跨复位有效、远程 unpair。修了两处上板问题：TRNG 未播种导致 rng_error；BlueZ 的 Just Works 需要 agent 授权（脚本自带 D-Bus agent）。板上现跑 M2 固件，处于开放模式（未配对）。
- 联调用 UGREEN 蓝牙适配器（RTL8761B），靠补丁版 btusb + 手工放的 rtl8761bu 固件才能用，见操作手册 6.8；换内核要重做。
- 两仓 2026-11-11 均已推送：Weband `origin/main` = `dba20aa`；open-company `fork/main`。

## 等待项（等人）
1. 采购 P1 外设（见 `goal.md`），不阻塞 P0。按 V1：麦已有（3037 模拟麦）；缺 JDI387A 圆屏 + 转接。充电要换锂电版芯片的板子（如 SF32LB52-DevKit-LCD）+ 锂电池，是否购买待用户决定。不再需要 PDM 麦、JD7601、LGS4056。
2. 下一个里程碑待用户选：M3 固件（VAD + Opus 录音，外设已齐）、M4（缺 JDI 圆屏；充电在 Nano 上 blocked）、M5（OTA / DFU）。

## 下一步
- 等用户选下一个里程碑（见等待项 2），在独立 worktree 开工。
- 复测 M2：板上已是 M2 固件且处于开放模式，`python3.10 scripts/ble_m2_check.py --reboot --unpair`（需 UGREEN 适配器，见操作手册 6.8）。

## 证据索引
- 每步实测记录：`/home/whole/data/reawork/weband/evidence/digest.md`
- 构建日志：`evidence/build_nano_n16r16.log`、`evidence/build_weband.log`
- 烧录与回读：M0 `flash_hello_world.log` / `flash_readback.txt`；M1 `flash_weband.log` / `flash_readback_weband.txt`
- 串口：`evidence/hello_world_boot_1000000.log`、`evidence/weband_boot_1000000.log`、`evidence/key_monitor.log`
- 出厂备份：`evidence/factory_flash_first4MB.bin`（不入库）

## 卡点 / 风险
- V1 纸面核实已完成（2026-11-10，Weband `docs/hardware-inventory.md` C5，证据 `evidence/nano_sch/`）：模拟麦可直接接 J1-4/5（板上有 2.2 µF 隔直，MIC_BIAS 1.4–2.8 V）；JDI 14 根信号都已引出；**Nano 芯片不带充电，M4 充电部分在 Nano 上 blocked**。
- IMU：V1 固件反汇编确认不访问 LSM6DS3TR-C（0x6A），不对标（证据 `/home/whole/data/reawork/refdevice-v1/analysis/imu_findings.txt` 及同目录脚本）。
- M3 硬件链路实测通过（2026-11-10）：板上烧了 SDK `audprc` 例程（非 hello_world），3037 模拟麦经 MIC_BIAS 供电能拾音，安静 −51 dBFS、出声 −31…−23 dBFS；导出的 8 kHz WAV 用户试听正常（Weband `evidence/digest.md`）。新增 `scripts/serial_capture.py`、`scripts/pcm_stats.py`，修了 `scripts/build.sh` 传参 bug，均未提交。
- 仍未核实：MIC_BIAS 电压值（没有万用表，只间接确认可用）；JDI387A 屏自身的供电与 VCOM 要求（需屏规格书）；V1 电源键是否 PA34。
- BLE 协议逆向基于 V2 固件，M2 用到时要拿 V1 固件字符串（`/home/whole/data/reawork/refdevice-v1/v1_strings.txt`）复核命令与状态串。
- refdevice 长按电源键的时长没有证据；KEY1 按住 10 s 会硬件复位，长按动作必须在此之前触发。
- refdevice 应用源码私有，M2 起按逆向协议净室重写；无证据的字段标 `TODO(weband)`。
