# Weband 产品约定（AGENTS.md）

## 一、产品定位
`Weband` 是对标 refdevice 的自有硬件产品，运行在 SiFli SF32LB52X（Cortex-M、RT-Thread）上。**硬件对标 refdevice V1（圆屏）**（2026-11-10 用户决定），不对标 V2（方屏）。

refdevice 有两版硬件，外设不同，固件也是分开的：

| | V1 圆屏（对标） | V2 方屏（不对标） |
|---|---|---|
| 板级名 | `sf32lb52-refboard-v1` | `sf32lb52-refboard-v2` |
| 参考固件 | `1.15.35-v1-round-serial` | `2.15.12-v2-square-serial` |
| 麦克风 | 模拟 MEMS 麦（LMA2718T421-OA5-2），`MIC_BIAS` 供电、`MIC_ADC` 输入，走片内 audcodec/audprc | PDM 数字麦（pdm1） |
| 显示 | JDI 圆形 LCD `jdi387a`（SDK：1.2 寸 240×240，JDI 并行接口） | JD7601 墨水屏（SPI） |
| 充电 | 片内 PMU 充电（固件引用 `bf0_hal_pmu.c`，有 CC/预充/目标电压/OVP/出厂校准日志）。片内充电只有锂电版芯片 SF32LB520/523/525/527 才有，所以 V1 用的是其中一款（具体型号为推断） | LGS4056（GPIO） |
| IMU | 原理图有 LSM6DS3TR-C（I2C 0x6A，`IMU_INT`），但**固件不访问它**：反汇编确认 I2C1 驱动虽注册，却没有任何应用代码打开总线或以 0x6A 读写（`refdevice-v1/analysis/imu_findings.txt`） | 无证据 |

两版共有的功能面：BLE 配对 / 鉴权 / 解绑 / OTA 窗口控制、录音（WebRTC VAD + Opus）、壁纸传输、电源键（单击 / 双击重置配对 / 长按）与充电管理。BLE 协议与录音后端的逆向分析（`refdevice_固件反汇编分析.md` 等）是基于 V2 固件做的，用到 V1 时要用 V1 固件字符串复核。

当前阶段只做**固件**。手机端先沿用资料里已有的 `reconstructed-project` 骨架，不在本阶段排期。

**手机端协议兼容原版**（已确认）：固件与原版 App 之间的线协议保持兼容，即 `MBWP` 二进制壁纸帧、JSON 控制命令（`pair_begin` / `pair_commit` / `auth` / `unpair` / `arm_ota` 等）及其已有证据的状态串。兼容只指线协议；不分发原版 App，也不使用其名称与图标。逆向资料没有给出的字段名与状态串，按 `design.md` 的做法自行定义并标 `TODO(weband)`，登记为"自有定义"，联调时若与原版 App 不符再回头修正。

中文回复用户，如果翻译不准确可以保留英文

## 二、硬件与资料

- **现有开发板**：SF32LB52-DevKit-Nano，已通过 USB Type-C 接入本机，枚举为 CH340 串口 `/dev/ttyUSB0`（`1a86:7523`，稳定别名 `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`），当前用户在 `dialout` 组，串口下载通路已用 `sftool` 只读验证通过。
- **板型已确认**：`sf32lb52-nano_n16r16`（芯片 SF32LB52JUD6，16 MB NOR + 16 MB PSRAM），依据是用户购买信息。`sftool` 的地址探测不能区分容量，没有用它作判据；若上板行为与 16 MB PSRAM 不符，再以芯片丝印复核。
- **串口控制台**：`uart1`，波特率 **1000000**（构建配置 `CONFIG_RT_SERIAL_DEFAULT_BAUDRATE`），连接命令 `python3 -m serial.tools.miniterm --rts 0 --dtr 0 --eol CR /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 1000000`（pyserial 3.5，装在用户目录），退出按 `Ctrl+]`。
  - **不要用 `screen`**：本板 RTS 接复位，`screen` 打开串口时会拉有效 RTS 且无法关闭，芯片被一直按在复位里，表现为"回车没反应"（实测 RTS 有效时 0 字节输出，释放后正常出 `msh />`）。
  - 关闭终端窗口不会退出 `screen`，它会转入后台继续占着串口；用 `screen -ls` 查、`screen -S <id> -X quit` 退出。
  - 同一时间只能有一个程序占用串口，烧录前先退出终端。
- **只读资料根目录**：`/home/whole/data/reawork/refdevice`
  - `固件从源码编译成功报告.md`：已跑通的 SDK v2.5 + arm-none-eabi-gcc 14.2.1 构建流程与踩坑记录
  - `analysis/固件构建与烧录参考.md`：分区表、烧录地址、`sftool` 用法
  - `refdevice_固件反汇编分析.md`：BLE 协议、鉴权、配对、OTA 窗口、关键 RAM 状态
  - `.agents/tasks/refboard-v2/design.md`：已有的 refboard-v2 板级与驱动设计（含"哪些引脚是假设"清单）。**这是 V2 的设计**，PDM、JD7601、LGS4056 部分不适用于 V1；BLE 应用部分仍可参考。
  - `sifli-sdk/`：SiFli-SDK `release/v2.5` 的本地副本（2.2 GB，只读使用，不在其上直接改）
  - `refdevice-firmware-2.15.12-v2-square-serial.zip`：V2 固件，以上逆向分析的对象。
- **V1 只读资料**：`/home/whole/data/reawork/refdevice-v1`
  - `refdevice-Firmware-1.15.35-v1-round-serial.zip`（来源 `github.com/refvendor/refdevice` release `v1.5.0`，SHA-256 `5b28352d…de832e`），解压在 `fw/`，`firmware-manifest.json` 写明板级 `sf32lb52-refboard-v1`。
  - `v1_strings.txt` / `v2_strings.txt`：两版 `main.bin` 的 `strings -n 4` 输出，用来对比外设。
  - `analysis/`：V1 反汇编脚本（`python3.10` + capstone，基址 `0x12020000`）与结果。`imu_findings.txt` 记录了 I2C 调用链的定位地址（`rt_i2c_transfer` `0x1207efb4` 等）。
  - 原理图截图 `/home/whole/share/mic_imu.webp`（V1 的麦克风与 IMU 部分）。
- **工作目录**：`/home/whole/data/reawork/weband`（已确认并创建）。建仓后在 `Productfile.yaml` 补 `source.git`。
  - `sifli-sdk/`：从 `refdevice/sifli-sdk` 本地克隆，分支 `weband-base`，固定在上游 `release/v2.5` 的 `87d5700a`，**不含**原目录里 `seiyamiro` 的 4 个自有提交（refboard 板级、协议核心与主机测试）。M2 需要时从那 4 个提交里挑选移植。子模块 URL 已指向本地 `.git/modules`，推送到远端前需改回官方地址。
  - `evidence/`：探测、备份、构建与烧录证据。
- **本机工具链**（SiFli SDK 已安装）：`~/.sifli/tools/arm-none-eabi-gcc/14.2.1`、`~/.sifli/tools/sftool/0.2.5/sftool`；`source export.sh` 即可编译。
- **出厂备份**：`evidence/factory_flash_first4MB.bin`（SHA-256 `0343fa70…913c01`）。出厂内容只占 `0x12000000–0x12090000`，该备份已完整覆盖，可用来还原。

### 与原厂板的差异（必须先正视）
对标的 V1 原厂板 `sf32lb52-refboard-v1` 有：模拟 MEMS 麦（`MIC_BIAS` / `MIC_ADC`）、JDI387A 圆形 LCD、片内 PMU 充电 + 电池、电源键、LSM6DS3TR-C IMU。DevKit-Nano 板上这些器件都没有。2026-11-10 按 Nano 原理图、SiFli 硬件设计指南与 SDK 核对（纸面，未实测，详见 Weband 仓库 `docs/hardware-inventory.md` C5）：
- **模拟麦可直接接**：J1-4 = `MIC_ADC`（板上已串 2.2 µF 隔直电容 C15），J1-5 = `MIC_BIAS`（输出 1.4–2.8 V）。
- **JDI 并行屏引脚都引出了**：FPC 上 PA02–PA08，J2 上 PA39–PA43，FRP/XFRP 在 J1 的 PA24/PA25。屏的供电与 VCOM 要看屏的规格书。
- **Nano 不能做充电**：SF32LB52JUD6 是标准供电版，芯片不带充电；板上 PVDD 接 3.3 V LDO，`VBATS` 悬空。要验充电需换锂电版芯片的板子（如 SF32LB52-DevKit-LCD，SDK 中为 SF32LB525UC6 / 527UD6）。
- V1 的完整引脚表没有证据（只有原理图里的麦克风和 IMU 两块）；电源键是否同为 PA34 未在 V1 固件中核实（日志是运行期 `pin=PA%d`）。原厂 NOR 布局里 `dfu` 在 `0x12720000`，需要至少约 8 MB 的 NOR；若选到 4 MB 的 `nano_n4` 变体放不下，必须按实际容量重排分区。

## 三、里程碑与优先级

### P0（仅靠 DevKit-Nano 即可验收）
- **M0 构建烧录基线**：SDK v2.5 + 工具链 14.2.1 在 Nano 板上编译 `hello_world`，经 `sftool` 烧录，串口出现示例 `main.c` 打印的 `Hello world!`，且启动横幅的构建日期与 commit 与本次构建一致、`msh />` 可交互。（`Hello RT-Thread!` 只是镜像里的字符串指纹，示例启动时不会打印，不作判据。）
- **M1 板级工程与外设清点**：从 `nano_*` 克隆出 `weband` 板级；盘点 DevKit-Nano 实有外设，缺哪些写进文档；分区表按实际 Flash 容量核对（16 MB NOR 能原样放下 refdevice 布局，不重排）。
  - 板级 `sf32lb52-weband` 在 Weband 仓库 `boards/` 下，**树外**，经 `--board_search_path` 接入，SDK 不改动；构建统一用 `scripts/build.sh`（会校验 SDK commit）。
  - 外设清点结果见 Weband 仓库 `docs/hardware-inventory.md`：BLE、PSRAM、电源键 PA34 板上就有。第 2 节已按 V1 改写（模拟麦、JDI 圆屏、片内充电、IMU），V2 的 PDM / 墨水屏 / LGS4056 引脚移到 2b 只作记录；V1 待核实项见 C5。
- **M2 BLE 控制协议**：实现 `pair_begin` / `pair_commit` / `auth` / `unpair` / `arm_ota`（5 分钟窗口）与 `MBWP` 二进制壁纸帧的会话与访问控制；配对令牌持久化。

### P1（需要外设到位，不阻塞 P0）
- **M3 音频链**：模拟麦经片内 audcodec ADC 采集 → VAD → Opus 编码录音。
- **M4 显示与电源**：JDI387A 圆形 LCD（或同接口的 JDI 屏）、PA34 电源键（单击 / 双击 / 长按语义）、片内 PMU 充电 + 锂电池。充电部分在 Nano 上无法验收（芯片不带充电），需换锂电版芯片的板子，否则记 blocked。
- IMU（LSM6DS3TR-C）：V1 原理图有，V1 固件经反汇编确认不访问，不在对标范围内，不排期。
- **M5 OTA / DFU**：`dfu` 分区校验与安装。

### 明确不做
- 不把原厂镜像（`main.bin` / `dfu.bin` / `ftab.bin` / `bootloader.bin`）刷到 DevKit-Nano。
- 本阶段不做手机端 App、不做量产与外壳。

## 四、红线

1. **净室实现**：原厂二进制、APK、Ghidra 反编译 C 只留在 `/home/whole/data/reawork/refdevice` 与 `/home/whole/data/reawork/refdevice-v1` 供阅读，**不得提交进 Weband 仓库，也不得出现在任何 Release**。代码按协议行为与 SiFli-SDK 公开 API 重写，不复制反编译代码。
2. **推断不当事实**：分析报告里标"推断"的函数名、字段名、状态变量，在 Weband 代码里一律标 `TODO(weband)` 并在 digest 登记。无证据的线格式（如鉴权的比对算法）由我们自行定义时，要明确写成"自有定义"。
3. **不用 refdevice 名称与图标**：对外产品名只用 Weband。
4. **烧录安全**：烧录前确认芯片型号、串口端口与板型，并先向用户确认；不手写分区地址，一律取自构建产物；不改 `ftab` / bootloader 地址，除非有证据。
5. **没有板子或外设就记 blocked**：不用模拟结果代替真机结果。
6. **禁止跑到绿为止**：同一个失败重试不超过 2 次，之后写出根因再换方案。

## 五、交付质量底线（对公司准则的固件适配）

1. **真机闭环**：编译通过不算达标。达标 = 编译 → 烧录到真实开发板 → 串口日志证据 →（M2 起）经 BLE 联调走通 `pair → auth → ok`。
2. **构建可复现**：固定 SDK 分支 `release/v2.5` 与具体 commit、工具链 `arm-none-eabi-gcc 14.2.1`，构建命令写进文档。
3. **证据落盘**：串口日志、烧录日志、产物 SHA-256，每完成一步追加进当场 `digest.md`。
4. **能单测的先单测**：协议解析、会话状态机这类纯逻辑，先写成可在 PC 上跑的单测，再上板，不把它留给真机调试代劳。
5. **并行开发**：每个研发工作项在独立 `git worktree` 里完成，再合回主分支。

## 六、值班任务
本产品的任务都需要真实开发板在线，不适合无人值守，所以**不挂 cron，手动触发**：
1. `firmware-build-flash`（构建、烧录、串口验证）
2. `firmware-port`（按 brief 指定的里程碑移植一项功能）

建立公开 GitHub 仓库后，再按公司准则补盯盘与发版类任务。
