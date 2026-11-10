# Weband 交接记录

最近更新：2026-11-10

## 现状
- M0 已完成（2026-11-09）：hello_world 在 Nano 上编译、烧录、回读一致、串口启动正常。
- M1 已完成（2026-11-10）：
  - 树外板级 `boards/sf32lb52-weband`，编译通过；除板名与 LED 极性外与 SDK 的 Nano 板等价。
  - 分区表核对：16 MB NOR 原样放下 refdevice 布局，不重排。
  - 外设清点 `docs/hardware-inventory.md`；真机核对：LED（PA31/PA32）低电平点亮，KEY1=PA34、KEY2=PA33 按下为高。
  - weband 版已烧录上板：三区回读一致，串口启动、`Hello world!`、`msh />` 正常。
- 板上当前运行的是 `sf32lb52-weband` 版 hello_world。

- 首次提交已完成（2026-11-10）：`main` @ `a6f1c46`（两个提交已合并为一个），38 个文件；SDK、Flash 镜像、板图不入库。
- 远端：`origin` = `git@github.com:aadnapp/weband.git`（私有）。2026-11-10 已推送 `main`，远端与本地同为 `a6f1c46`。

## 等待项（等人）
1. 采购 P1 外设（见 `goal.md`），不阻塞 P0。
2. M2 开工需要用户触发（`#task-firmware-port`，brief 写 M2 与要实现的行为）。

## 下一步
- M2（BLE 控制协议）在独立 worktree 开工：先写主机单测，再上板联调 `pair → auth → ok`。

## 证据索引
- 每步实测记录：`/home/whole/data/reawork/weband/evidence/digest.md`
- 构建日志：`evidence/build_nano_n16r16.log`、`evidence/build_weband.log`
- 烧录与回读：M0 `flash_hello_world.log` / `flash_readback.txt`；M1 `flash_weband.log` / `flash_readback_weband.txt`
- 串口：`evidence/hello_world_boot_1000000.log`、`evidence/weband_boot_1000000.log`、`evidence/key_monitor.log`
- 出厂备份：`evidence/factory_flash_first4MB.bin`（不入库）

## 卡点 / 风险
- refdevice 长按电源键的时长没有证据；KEY1 按住 10 s 会硬件复位，长按动作必须在此之前触发。
- refdevice 应用源码私有，M2 起按逆向协议净室重写；无证据的字段标 `TODO(weband)`。
