# kicad-happy 辅助设计阶段报告

**结论：不能使用或打样。本轮完成工具接入、原生文件修复、一个电源外围改动和音频页真实引脚落地；不是整板设计完成或完整逐器件放行。**

来源：[aklofas/kicad-happy](https://github.com/aklofas/kicad-happy)，固定commit `a6bba1add1e18b89e3aa0824b9769ed1d9d79174`。已使用skill-installer安装 kicad、datasheets、emc、spice、bom 到个人skills目录。安装不修改项目依赖；本轮实际使用kicad、datasheets方法及emc工具，未进行采购或发布。

## 阻断项

| 优先级 | 问题 | 证据 |
|---|---|---|
| 必须完成 | 原理图126个器件，PCB只有21个测试焊盘和4个孔，缺105个器件封装 | KiCad原生drc.json的schematic_parity；cross.json的XV-001一致 |
| 必须完成 | SIM8230C、LCD、SIM卡座、触摸控制器、麦克风仍没有真实引脚电路 | 原始各分层图与设计清单；它们不会出现在上述126个器件中。ES8311/PAM8302A 本轮已按手册落成真实引脚，但仍无封装、无官方放行件 |
| 必须完成 | U6.TS/BAT_NTC只有U6.1，没有实际电池NTC连接 | 原生XML网表、技能网络数据、deep_review证据门禁 |
| 必须决策 | Modem的开机/复位/状态三路缺GPIO；电平域未定 | PIN_MAPPING.md；保持SOS/AI独立GPIO |
| 必须完成 | 缺ESD/TVS、具体连接器、全器件placement、介质层叠、RF与布线 | 原始工程；manufacturing目录仍无生产数据 |
| 必须决策 | SIM占位超出板边且与模块重叠、电池/表壳高度未知 | PCB_LAYOUT.md；不能靠脚本自动移动或缩小封装解决 |

## 相比上一版

已修正测试点非法位号、三组并联电源脚ERC建模、安装孔自冲突keepout、库封装一致性和丝印/导线显示。已给十颗有明确型号的IC补充MPN和Manufacturer字段，关联已下载官方PDF。

新增R109=100k，给U7的EN与PS/SYNC共用串联电阻。几何DRC从34减到0。06_AUDIO 整页按 ES8311 Rev 5.0 与 PAM8302A DS41333 Rev.6-2 落成真实引脚（U9 20脚、U10 8端、C601–C614、R601），并给 GND/VBUS_5V 增加 PWR_FLAG 声明：KiCad原生ERC从188降到155（错误40→28），器件109→126，网络120→129，导线384→427。parity由87升到105，多出的17项正是音频页新器件还没有封装，属于显式缺口而非掩盖。U4 VBACKUP 与 U6 TS 两项按器件要求保留，理由见 ERC_DRC_REPORT.md 的 waiver 记录；其余错误全部是未画实的器件接口。

## 执行记录

| 项目 | 实际执行 | 边界 |
|---|---|---|
| analyze_schematic.py | 完成，126器件/129网络/427导线；75项findings（4 error、23 warning、48 info），保存为 schematic.r111.json | 与原生网表器件数相符；开放意图标签与NC会导致网络统计口径不同 |
| analyze_pcb.py --full | 完成，25个footprint、0 tracks、0 vias；18项findings（16 KO-001、1 TE-001、1 FD-001） | 没有真实IC placement，不是完整布局审核 |
| cross_analysis.py | 完成，XV-001指出105个原理图器件未上板 | 与KiCad原生parity数量一致；不含未画符号的器件 |
| analyze_emc.py | 完成，8项（2 error、3 warning、3 info），风险评分77.5 | 无走线/地平面/射频模块引脚；EMC评分不具备放行意义 |
| analyze_thermal.py | 完成，只估算U7（tj≈44.0°C，全板0.127W），其余1项跳过 | 缺封装、铜皮、负载和表壳；不接受其100分或该结温为证明 |
| lifecycle_audit.py --only lcsc | 完成，10种IC全部 unknown | 该来源不能提供可靠生命周期结论，没有宣称active |
| diff_analysis.py | 完成，修复前快照→r111：新增21项、移除0项，自动标记 breaking、7项 regression | 自动标签只是告警分类变化（多为新增音频器件）；不是硬件功能回退结论 |
| Deep Review / evidence gate | U6/U7局部审核；3条证据通过门禁、0隔离项 | 门禁必须传 `--project-dir .`，否则 analysis/helpers/check_power.py 被解析成不存在、三条全部误判为隔离；仅对这三条结论负责 |
| SPICE | 未运行 | PATH未发现ngspice、ltspice、xyce；没有声称仿真通过 |
| Gerber分析 | 不适用 | 按设计阶段禁止输出制造文件，目录中只有发布门禁说明 |
| 结构化datasheet extraction | 未完成 | 使用官方PDF直接阅读；自动分析显示datasheet_backed=0，不能把启发式结果称为datasheet证明 |
| validate_draft.py（项目自有） | 通过，但只是 PASS_STATIC_ONLY：16个S表达式、147行BOM、453行引脚/意图、128个含引脚符号、21测试焊盘、4个NPTH | 不替代原生ERC/DRC、封装与电气验证 |

原始自动结果保存在本地 `analysis/kicad-happy/`，未改写误报原文。该目录是忽略的可再生分析缓存；耐久证据在 `analysis/deep_review.json`、`analysis/helpers/check_power.py`。原生检查源文件哈希在 `docs/NATIVE_CHECK.json`。

## U6/U7 电源逐项审核

| 核对项 | 结果和边界 | 来源 |
|---|---|---|
| U6 physical pins | 引脚表与当前符号一致；EP实际footprint编号仍未确认 | BQ24074 SLUS810N pp7–9，Table7-1 |
| U6 ISET / ILIM | 890/1780=0.500A；1610/1620≈0.994A，均为典型值而非保证输出 | BQ pp12–13电气表；现有R101/R102 |
| U6 TS | 当前仅一端，不能实现电池温度监测 | BQ p9；BAT_NTC网络 |
| U6默认配置 | TMR、ITERM留空是允许的默认模式；没有关闭安全计时 | BQ pp8–9、13、27 |
| U7 pin1/14 | 之前直接接SYS；现为SYS→100k R109→DCDC_CTRL→pin1/pin14 | TPS63070 SLVSC58B p11 §8.4.2、p12 §8.4.5，允许共用串阻 |
| U7分压 | 0.8×(1+470k/150k)=3.306667V，保留原值 | TPS p17 §9.2.2.1/Table4 |
| U7滤波 | 1.5µH；本地输出名义54µF。仅名义值不能证明有效电容、饱和、瞬态或稳定性 | TPS pp4、17–19；磁件/电容MPN和布局未完成 |
| U7封装 | 9/10/11为大功率焊盘；没有再造一个无依据的EP | TPS p3顶/底视图；仍未实现真实land pattern |

R109是修正厂商**推荐接法**，不是证明旧接法必然失效。所有电容/磁件的具体料号、DC bias、温升和负载测试仍缺。

## 自动结果的人工纠正

1. **TPS63070 Vref误判**：脚本选择heuristic 0.6V，得到2.48V。实际手册是0.8V，得到3.307V；不能据该误报改R105/R106。
2. **16个KO-001误报**：脚本用包围盒判断四孔落入四段环形区域，忽略中间孔洞。实际区域内半径0.75mm，钻孔半径0.7mm；原生DRC没有对应冲突。没有移动用户指定安装孔，也没有降低间距规则。
3. **2个PP-001与1个VM-001（本轮新增判定）**：都源于同一个命名启发式——`is_power_net_name()` 认识 VSYS/VBAT/VMAIN，但不认识裸名 SYS。原生网表证明 SYS 由 U6.11（OUT，power_out）驱动，带 C103/C105/C106/C107 大电容并接入 U7.12/13（VIN），直流供电路径真实存在；该器件只是不在脚本的电源名白名单里。VM-001 又称 U6 是 5.0V 域、U7 输出 3.3V，但 SYS 上的器件只有 U6.OUT 与 U7.VIN，充电截止 4.2V 在 TPS63070 输入范围内，没有数字信号跨越该rail。因此未据此改动网络名、供电器件或加电平转换器；是否把 SYS 统一改名为 VSYS 属于命名规范决策，留待与 D10/D13 一起定案。
4. **routing_complete=true**：只看当前测试点得到无待连对象，不代表全板布线完成；实际有0根线、105个器件未上板。该自动字段不得作为验收依据。
5. **热评分100/100**：只有一个器件的启发式估算，无有效负载/封装/布局，丢弃整板安全推断。
6. **EMC的77.5评分、150MHz和48mm建议**：未包含真实5G/Wi-Fi RF链路，不能作为天线或缝合过孔设计参数；返回路径缺数据是未布线造成，不是再次添加--full就能修复。
7. **FD-001贴片基准点建议**：当前所谓21个SMD均为裸PCB测试焊盘，不是21个贴片器件。最终装配应另外审核fiducial，本阶段不能据此增加任意器件。
8. **生命周期unknown**：保持未知，不推断停产或在产。
9. **SS-001（未判为误报）**：BOM 36个唯一料号里只有10个带MPN（27.8%），这是真实采购阻断，必须靠 D01–D05、D09–D13 的选型与料号收口，不能靠填猜测MPN清除。

## 其余自动告警的人工判定

- **RS-001 ×3（真实缺口）**：RTC_VBACKUP、SIM_VCC、VBAT_MODEM 三条网络没有声明来源，对应 D09（电池包与负载）、D12/D13 的电源决策，不能靠加 PWR_FLAG 假装存在。
- **PU-001 ×3（不采纳）**：U6.TMR 按 BQ24074 允许留空使用内部默认计时；U7.EN 已由 R109 从 SYS 拉高，脚本要的是另一条上拉，不属于缺陷；U9.MIC1P 是模拟麦克风输入而不是开路信号线，按模拟麦克风手册处理。
- **analyze_connectivity 的 17 warning + 7 info（不掩盖）**：与原生 ERC 的 26 dangling/50 isolated/77 开放端点同源，全部指向未画实的显示、蜂窝、SIM、触摸与麦克风器件。

## 审核范围与下一步

本轮手册深审只覆盖U6/U7和音频页U9/U10的引脚表；U1/U3/U4/U5/U8/U11保留前轮电气草稿，不视为本轮完整逐项通过。没有针对全部料号完成结构化抽取和物理封装映射。未知芯片/连接器保持TBD，没有用相近型号填补。ES8311 依据的是标注 Confidential 的第三方镜像件（见 D04/D15），只可内部复核。

电源树仍为Pogo 5V→BQ24074→SYS→TPS63070→3V3，VBAT→MAX17048；拟议VBAT→modem路径尚未完成。Modem BAT负载对充电终止、欠压和热设计的影响仍需决策，不能凭本轮局部修复声称系统可靠。

下一阶段仍需补全资料和真实元件选型，完成GPIO/电源决策（含 D15、D16 的音频决策与 SYS 命名规范）、原理图、真实封装与全器件placement。之后才进行用户要求的Power/RF/Mechanical评审，再经确认进入布线。技能提供证据和检查，不代替这些工程工作。
