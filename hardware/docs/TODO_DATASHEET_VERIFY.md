# 资料和设计阻断项

2026-09-20。TBD 是必须继续处理的工作，不是 ERC/DRC waiver。没有真实引脚的图框不能流入制造网表。

| ID | 所需输入 / 动作 | 当前证据与被阻断内容 |
|---|---|---|
| D01 | SIMCom **SIM8230C 对应 SIM8230 硬件设计手册 V2.04** 或厂商更新版；含完整 pin table、NC/Reserved、IO voltage、PCM master、PWRKEY/RESET timing、参考电路、LGA/LCC land pattern、GND vias、RF guide | 已找到中文官网对应型号与下载项；下载要求登录。只核实产品级外形、供电范围与功能，U2 没有猜测引脚。不得用 SIM8230X-M2/PCIe 资料替代。 |
| D02 | LCD 确切模组规格书、FPC 连接器 MPN、触点侧、LED 串电压/电流、触摸控制器信息 | J_LCD_GENERIC 标签保留，无编号/封装；背光驱动未选型。 |
| D03 | Nano SIM 卡座 MPN、推荐焊盘、SIM 接点和机械检测脚定义 | 不能把卡片接触区编号直接当作某个卡座引脚；卡座尚未绘制。 |
| D04 | ES8311 官方发布版 datasheet/application note 与 QFN-20 land pattern | 引脚表已按 Rev 5.0（2019-03）镜像件核实，U9 已有 20 个真实引脚和去耦/参考/耦合外围草案。该镜像件页脚标有 Confidential 且经第三方重渲染，只能用于内部审核；制造封装、mic bias 与寄存器配置仍缺官方放行文件。 |
| D05 | Analog MEMS 麦克风 MPN、偏置/供电、声孔/焊盘 | MIC1 无真实引脚和声学孔。 |
| D06 | 官方 ESP32-S3-PICO land-pattern CAD/推荐 PCB 焊盘及装配建议 | v1.2 引脚、PSRAM 占用、外围图和 7×7 package 已查；机械端子图不直接当成焊盘图。U1 未绑定猜测封装。 |
| D07 | BQ24074 RGT、TPS63070 RNM、BMI270、MAX17048 TDFN、RTC C7、TLV75518 DBV、DRV2605L DGS 的精确 land pattern 二次审核 | 已绘制电气草稿，尚未创建/批准 IC PCB 封装。EP 命名到 footprint pad 编号、paste window、mask、courtyard、pin1 都必须核对。 |
| D08 | PAM8302A 确切封装与订货料号、声压/音质目标 | DS41333 Rev.6-2 引脚表已核实（1 SHDN_N、2 NC、3 IN+、4 IN-、5 VO+、6 VDD、7 GND、8 VO-），推荐工作电压 2.0–5.5V、绝对最大 6.0V、UVLO 2.1V。SO-8/MSOP-8/U-DFN3030-8 尚未选定，U10 仍无封装。内部 150k/10k 固定 23.5dB 增益，与 ES8311 满量程 0.4535Vrms 组合会在音量拉满前削顶：需按声学目标决定用寄存器衰减还是外加约 16kΩ RIN。 |
| D09 | 保护电池包规格、NTC B 值/公差、2.5A 脉冲条件、尺寸/高度、连接器 MPN | 温度边界、欠压策略、端子能力和电池覆盖区未验证。 |
| D10 | PCB 厂六层介质厚度/Dk/铜厚/阻焊、板厚和孔工艺 | 不猜 50Ω RF / USB 差分宽度；六铜层已建，介质层叠待定。 |
| D11 | 表壳、显示、天线、扬声器、马达、Pogo、按键、螺钉柱的 STEP/结构图 | 无法确认 keepout、整机厚度和 top/bottom 高度。当前 Nano SIM 分区冲突。 |
| D12 | 选择 UART/PCM 翻译器与控制接口 | 三路 modem 控制 GPIO 不足；需要审核复用 strap 或增加 I2C GPIO 扩展器，SOS 保持独立 MCU 输入。翻译器 OE/方向/关断隔离不能缺。 |
| D13 | ESD/TVS、RF 接头、充电保护、背光/音频外围、所有 R/C/L 完整 MPN | BOM 有采购占位但不可下单；容量、电流、耐压、偏置与实际封装必须闭合。 |
| D14 | 已解决工具安装；设计检查尚未通过 | KiCad 10.0.6已实际加载、导出网表、运行ERC/DRC。本轮 ERC 由185项降到155项（28 errors/127 warnings），parity 由88项升到105项（新增17个音频器件仍无封装）；见ERC_DRC_REPORT.md。 |
| D15 | ES8311 官方发布版对 die-attach/PGND 焊盘的编号与网络定义 | Rev 5.0 引脚表只有 1–20，但封装图有一个无编号的 exposed die-attach pad，典型应用图把它标成 21/PGND。U9 符号暂保留 20 脚，不猜编号；land pattern 与散热/接地判定必须一起关闭。 |
| D16 | 模拟地策略决策 | ES8311 典型电路要求 GND(SYS) 经 0Ω 到 AGND，并把该芯片当模拟器件布局。当前工程全板只有一个 GND 网络。是否引入 AGND_CODEC + 0Ω 星形接地点、以及它在六层叠层和 net-tie 上的落法，需要决策后再改原理图。 |

建议先提供 D01–D05、D09–D11，并对 D15/D16 两项音频决策给出方向。已公开的数据手册链接及文件哈希在 SOURCES.json；“下载成功”不等于整个器件设计已经核准。ES8311 本轮用的是第三方镜像件（页脚标 Confidential、由 PDFium 重渲染），只作内部引脚复核依据，供应商/认证/对外分发前必须换取官方发布件。

后续顺序：关闭器件和电源方案问题 → 完成真实符号及封装核对 → 补齐电路与 GPIO → KiCad ERC → 原理图同步 PCB → 全部器件 placement/3D/机械 review → 用户确认 → 按要求顺序布线 → DRC 与制造审核。不能因当前分区图好看而跳过中间步骤。
