# AIoT 老人智能手表 EVT V1 — KiCad 评审草稿（未完成的评审草稿）

**不能作为能工作的电路板使用，不能送厂打样。** 当前网表化126个器件，但PCB只有21个测试焊盘和4个孔；SIM8230C、LCD、SIM卡座、触摸控制器和麦克风仍是无引脚图框。105个器件封装未上板。

## 本轮实际进展

- 已用 KiCad 10.0.6 原生加载工程、导出网表和全部图纸，核对348个已连接引脚的网名。
- ERC：28 errors + 127 warnings（共155项），未通过。现有几何对象 DRC 为0，但 schematic-parity 有105项缺失封装，整板仍未通过。
- 修正三组重复电源输出的符号类型、TP1–TP21合法位号、孔周keepout与库封装一致性、丝印高度和导线显示。
- 按TI手册，为TPS63070的EN/PS_SYNC增加共用100k串联电阻R109。保持原有常开/省电模式。
- 06_AUDIO 按 ES8311 Rev 5.0 与 PAM8302A DS41333 Rev.6-2 落成真实引脚（U9 20脚、U10 8端）并补 15 个外围；GND/VBUS_5V 加 PWR_FLAG 声明；顶层 aiot-watch.kicad_sch 补成 A3 封面与层级索引页。
- 已安装并使用用户指定的kicad-happy技能；原理图、PCB、跨域、EMC、热分析和物料生命周期查询已运行。审核中排除了错误Vref、包围盒keepout、未布线“完成”等误报，未采用其评分作为放行依据。

## 打开与查看

打开 `aiot-watch.kicad_pro`，原理图入口为 `aiot-watch.kicad_sch`；00_TOP 下有九张功能图。实际板文件是 `pcb/aiot-watch.kicad_pcb`；根目录同名符号链接用于KiCad项目入口和原理图/PCB一致性检查。

`preview/00_TOP.svg` 至 `08_DEBUG_TEST.svg` 为KiCad原生输出。`PCB_TOP.svg`、`PCB_BOTTOM.svg` 为原生板层输出。部分图有同名PNG。`PCB_PLACEMENT.png` 是旧的分区说明图，不是3D或真实器件装配结果。

## 评审入口

- `docs/ERC_DRC_REPORT.md`：原生检查实测、修复与剩余问题。
- `docs/KICAD_HAPPY_REVIEW.md`：技能辅助审核、证据、误报与未覆盖范围。
- `docs/TODO_DATASHEET_VERIFY.md`：资料和设计阻断项。
- `docs/POWER_TREE.md`、`docs/PCB_LAYOUT.md`：电源、RF、布局和机械问题。
- `bom/BOM.csv`：147行采购/设计草稿，不可据此下单。
- `docs/PIN_MAPPING.csv`、`docs/NET_MATRIX.md`、`docs/aiot-watch.net.xml`：设计意图与当前部分电路的原生网表。

## 验证与后续边界

在仓库根目录运行 `python3 hardware/kicad/tools/validate_draft.py` 和 `python3 hardware/kicad/tools/check_kicad.py`。前者只检查结构；后者真实执行ERC、含schematic-parity的DRC、原生网表对照和图纸导出。目前后者退出码为5，不能改成忽略。原始JSON、命令日志与源文件哈希见 `docs/NATIVE_CHECK.json`。

STEP 1和BOM草稿已建立；真实封装、部分电路和全器件placement未完成。当前有六个铜层，但介质层叠/阻抗未定。尚未达到可放行的STEP 20。没有布线、覆铜、最终地过孔、3D装配校验或制造输出；布局确认前不进入Routing。

除安装用户指定技能外，项目变更仅在hardware目录。未启动项目服务、浏览器或硬件，未下单，未提交Git。
