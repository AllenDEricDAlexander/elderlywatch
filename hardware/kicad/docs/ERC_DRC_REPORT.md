# KiCad 原生验证报告

2026-09-20，KiCad 10.0.6。结论：**不可使用、不可打样；文件可读取不等于电路完整。**

## 实测

| 检查 | 初次原生检查 | 当前 | 边界 |
|---|---:|---:|---|
| 原生加载/图纸导出 | 原先未验证 | 成功 | 128个含引脚符号（其中2个是PWR_FLAG），网表导出126个器件 |
| ERC | 188 | 155：28 errors + 127 warnings | 未通过 |
| PCB几何DRC | 34 | 0 | 仅现有孔、测试焊盘、板框 |
| unconnected_items | 0 | 0 | 大多数器件没上板，不能代表连通 |
| schematic_parity | 87 | 105 missing_footprint | 音频页新增U9/U10和15个无源器件，全部仍未绑定封装 |
| 原生网表对照 | 未验证 | 126个器件、348个已连接引脚与清单一致 | 不含未知图框和NC；不证明物理封装正确 |
| 结构检查 | 15文件 | 16文件通过 | 不替代原生检查 |

原始结果：erc.json、drc.json、aiot-watch.net.xml。完整命令、退出码、源文件SHA256：NATIVE_CHECK.json。首次报告在checks/baseline，最新命令输出在checks/latest。

ERC、包含parity的DRC均返回5，表示仍有违规。原生网表和图纸导出返回0。不允许将退出码5写成通过。

## 本轮修复

1. BQ24074的BAT 2/3、OUT 10/11和TPS63070的VOUT 7/8分别是内部并联的同一电源端。每组保留一个power_out，第二引脚用passive表示，保留全部引脚/连线，消除三项重复独立输出冲突。
2. 测试点改成TP1–TP21，Value保留TP_5V等治具名称；网名和UUID不变，原生导出不再提示annotation错误。
3. 测试焊盘补齐与库一致的Fab/courtyard；新增NPTH_1.4mm库。修复21项库封装不一致和4项找不到库封装的问题。
4. 实心孔周keepout误禁自身NPTH，改成内径1.5mm、外径2mm的环形区域，每孔四个扇段，共16段。1.4mm钻孔位于中间空洞，环内仍禁止焊盘、线、过孔和覆铜；没有降低clearance。
5. 板名和孔位丝印高度调整到0.8mm；原理图导线显示宽度明确为0.1524mm，标题避开图框，电气端点不移动。
6. 根据TPS63070 SLVSC58B §8.4.2/§8.4.5新增R109=100k：SYS→R109→DCDC_CTRL→U7.1/U7.14。不是靠删除告警处理，而是补实际外围。

### 本轮新增：音频页与电源声明

7. 06_AUDIO 整页重画：U9 ES8311 按 Rev 5.0 引脚表落成 20 脚真实符号，U10 PAM8302A 按 DS41333 Rev.6-2 落成 8 端符号，并补 C601–C614、R601 共 15 个外围。原来的 MIC_ANALOG、CODEC_DAC、AMP_SUPPLY_TBD、AMP_ENABLE_TBD 四个占位网络被真实端点取代，新增 CODEC_DAC_P/N、CODEC_DACVREF/ADCVREF/VMID、CODEC_MIC_P/N、MIC1_P/N、AMP_IN_P/N、AMP_SD。单这一页消掉 10 个 label_dangling 错误和 18 个告警。麦克风、扬声器触点仍是无引脚图框，没有编造引脚。
8. 01_POWER 增加两个 PWR_FLAG（#FLG01→GND、#FLG02→VBUS_5V），声明这两路由板外（电池、触点连接器）引入，修掉 U1.57 与 U6.13 两项 power_pin_not_driven。VBAT 已由 U6.3 的 power_out 驱动，因此不加旗标。PWR_FLAG 设 in_bom no/on_board no，不进 BOM 和网表；库项直接取 KiCad 10 安装目录里的 power:PWR_FLAG 原文，避免 lib_symbol_mismatch。
9. U11 DRV2605L 的 REG（pin 1）由 passive 改成 power_out：它是芯片内部稳压器输出，不是无源端。07 页内嵌库副本同步修改。
10. 按本地 BQ24074 SLUS810N 电气表复核了 ISET/ILIM 系数（KISET 797/890/975 AΩ、KILIM 500mA–1.5A 档 1500–1610 AΩ、RILIM 有效 1.1k–8k），POWER_TREE.md 已按实测区间改写；未改任何电阻值。
11. tools/validate_draft.py 的“未核实器件禁止获得引脚”哨兵对 U9/U10 有意放宽：从禁止出现改成精确引脚集合断言（U9 必须恰为 1–20，U10 必须恰为 1–8），其余 U2/U12/U13/J2/J3/MIC1 仍禁止出现引脚。改动是刻意的，且仍会阻止任何额外的引脚漂移。
12. 顶层 `aiot-watch.kicad_sch` 原先只有一个 786 字节的空框（无标题栏、无内容），已补成正式的封面/层级索引页：A3 图幅、title_block（title/date/rev/company）、00_TOP 图纸框及其 8 个子页索引、电源树、各页状态、放行门禁与复现命令。根 UUID、00_TOP 的 sheet UUID、`(instances (project ... (path ... (page "2"))))` 与 Sheetfile 全部逐字保留，因此网表和标注不受影响；重跑后 ERC 仍 155 项、网表仍 126 器件/348 引脚核对一致。根页刻意不画符号、连线，也不加层级引脚：本设计的跨页连接靠全局标签，凭空加引脚会伪造一个并不存在的连接模型。生成脚本为 `tools/gen_root_sheet.py`（幂等，可重跑）。

手写 S 表达式时踩到两个 KiCad 10 解析约束，记录以免重复浪费时间在“加载原理图失败”上：`title_block` 内不接受 `(comment ...)`（写了就整图加载失败，注释只能放成页面文本）；粗体必须写成 `(effects (font (bold yes) (size x y)) ...)`，`(bold yes)` 放在 `font` 外面同样导致加载失败。

## 剩余ERC分类

| 类型 | 数量 | 原因和后续 |
|---|---:|---|
| label_dangling | 26 errors | 14 个网络：03 页 MODEM_PCM_CLK/DIN/DOUT/SYNC、MODEM_RESET、MODEM_STATUS、SIM_CLK/DATA/RST/VCC（SIM8230C 与 Nano 卡座均无引脚），05 页 TP_SCL/TP_SDA/TP_INT（触摸控制器未选型），06 页 MIC_SUPPLY_TBD（麦克风偏置待器件）。这些是接口意图，只能靠补真实器件电路关闭，不能靠改名或删除。 |
| pin_not_driven | 1 error | U6.TS/BAT_NTC只有U6.1；电池NTC接口未实现。不得用固定电阻冒充温度传感。 |
| power_pin_not_driven | 1 error | U4.VBACKUP。见下方 waiver 说明。 |
| unconnected_wire_endpoint | 77 warnings | 图框开放接口及未完成外围。 |
| isolated_pin_label | 50 warnings | 单端标签或缺少真实接收器件。音频页新增的 4 条是 MIC1_P/MIC1_N：耦合电容已连，麦克风本体仍是 TBD。 |

## 两项已记录的 ERC waiver

`aiot-watch.kicad_pro` 的 `erc_exclusions` 仍为 `[]`，`validate_draft.py` 断言这一点。以下两项不是抑制，而是带理由的接受：

1. **U4 pin 6 VBACKUP（power_pin_not_driven）**：MicroCrystal RV-3028-C7 应用手册规定，在没有备份电源时必须经 10kΩ 接到 VSS，不能让该脚悬空。当前实现就是 R402=10k 到 GND，因此该告警是器件要求的接法与 ERC 规则冲突，保留并记录。若改为纽扣电池或超级电容供备份，需要单独的电源决策。
2. **U6 pin 1 TS（pin_not_driven）**：TS 是电池包 NTC 的采样端，只有 U6.1 一个引脚在网络上。用固定电阻或上拉“喂”它会伪装温度保护，违反安全要求。关闭条件是 D09 的电池包 NTC B 值/公差与连接器资料。

105项缺失封装包括已有公开资料但尚未完成的部分，不能全归因于用户缺资料。未画出真实符号的U2/U12/U13/J2/J3/MIC1等不计入105项，不能由这个数字推断全部完成度。

原生ERC JSON中部分坐标与原图mm值不一致，定位以器件/引脚、items.uuid及原生图纸为准；未改原始报告。

## 复现

仓库根目录：`python3 hardware/kicad/tools/validate_draft.py`、`python3 hardware/kicad/tools/check_kicad.py`。

check_kicad.py明确启用 `--schematic-parity --severity-all --exit-code-violations`，保存网表/图纸与哈希，不生成制造文件。当前几何0违规绝不是整板0问题。
