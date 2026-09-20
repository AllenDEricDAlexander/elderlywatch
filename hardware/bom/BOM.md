# BOM 草稿 — 禁止据此下单

MPN/封装尚未完整选择；未知模块是采购占位。TP1–TP21 Value 保留治具名称。

| Reference | Value | Category | DNP | Notes |
|---|---|---|---|---|
| U6 | BQ24074RGTR | IC | No | EP physical pad identifier requires footprint review; TMR and ITERM open use defaults; Electrical draft; land-pattern release pending |
| U7 | TPS63070RNMR | IC | No | No separate invented EP; pins 9/10/11 are large power pads; Electrical draft; land-pattern release pending |
| U8 | TLV75518PDBVR | IC | No | 1V8 is optional auxiliary rail, NOT presumed to equal modem VDD_EXT; Electrical draft; land-pattern release pending |
| U5 | MAX17048G+ | IC | No | Powered/sensed from VBAT, not 3V3; Electrical draft; land-pattern release pending |
| J5 | BATTERY + NTC | Connector | No | NOT RELEASED: no pin-bearing symbol; Exact connector and pack NTC curve required |
| D1 | POGO INPUT TVS | TVS | No | NOT RELEASED: no pin-bearing symbol; Select standoff/clamp/leakage; not fitted electrically until selected |
| R101 | 1.78k 1% | Resistor | No |  |
| R102 | 1.62k 1% | Resistor | No |  |
| R103 | 10k | Resistor | No |  |
| R104 | 10k | Resistor | No |  |
| C101 | 4.7u 16V | Capacitor | No |  |
| C102 | 10u 10V | Capacitor | No |  |
| C103 | 10u 10V | Capacitor | No |  |
| L101 | 1.5uH / Isat TBD | Inductor | No |  |
| R105 | 470k 1% | Resistor | No |  |
| R106 | 150k 1% | Resistor | No |  |
| C104 | 100n | Capacitor | No |  |
| R107 | 100k | Resistor | No |  |
| C105 | 10u 10V | Capacitor | No |  |
| C106 | 10u 10V | Capacitor | No |  |
| C107 | 10u 10V | Capacitor | No |  |
| C108 | 22u 10V | Capacitor | No |  |
| C109 | 22u 10V | Capacitor | No |  |
| C110 | 10u 10V | Capacitor | No |  |
| C111 | 1u | Capacitor | No |  |
| C112 | 1u | Capacitor | No |  |
| C113 | 100n | Capacitor | No |  |
| R108 | 10k | Resistor | No |  |
| R109 | 100k | Resistor | No | Shared EN/PS_SYNC series resistor; TI SLVSC58B sections 8.4.2 and 8.4.5 recommend 1k-1M; final resistor MPN/footprint pending |
| U1 | ESP32-S3-PICO-1-N8R8 | IC | No | GPIO0/3/45/46 reserved for strap behavior; GPIO33-37 and SPICS1 are internal PSRAM; Electrical draft; land-pattern release pending |
| R201 | 10k | Resistor | No |  |
| C201 | 1u | Capacitor | No |  |
| R202 | 10k | Resistor | No |  |
| R203 | 4.7k | Resistor | No |  |
| R204 | 4.7k | Resistor | No |  |
| R205 | 0R / tune SI | Resistor | No |  |
| R206 | 0R / tune SI | Resistor | No |  |
| C202 | 22u | Capacitor | No |  |
| C203 | 100n | Capacitor | No | Locate at U1 supply pin 2 |
| C204 | 100n | Capacitor | No | Locate at U1 supply pin 3 |
| C205 | 100n | Capacitor | No | Locate at U1 supply pin 20 |
| C206 | 100n | Capacitor | No | Locate at U1 supply pin 46 |
| C207 | 100n | Capacitor | No | Locate at U1 supply pin 55 |
| C208 | 100n | Capacitor | No | Locate at U1 supply pin 56 |
| U2 | SIM8230C | IC | No | NOT RELEASED: no pin-bearing symbol; V2.04 required; no alternate SIM8230 pin map imported |
| J2 | J_SIM Nano SIM | Connector | No | NOT RELEASED: no pin-bearing symbol; Socket MPN/contact map required; eSIM mechanical option unallocated |
| U12 | MODEM IO TRANSLATOR TBD | Level translator | No | NOT RELEASED: no pin-bearing symbol; Direction, OE, VDD_EXT, power-off protection and PCM master TBD |
| D2 | SIM ESD ARRAY TBD | ESD | No | NOT RELEASED: no pin-bearing symbol; Low capacitance; socket-side; no invented array pin map |
| C301 | TBD C / DNP | Capacitor | Yes |  |
| R301 | 0R | Resistor | No |  |
| C302 | TBD C / DNP | Capacitor | Yes |  |
| ANT1 | RF CONNECTOR TBD | RF connector | No | NOT RELEASED: no pin-bearing symbol; U.FL/MHF4 exact part and land pattern not selected |
| C303 | TBD C / DNP | Capacitor | Yes |  |
| R302 | 0R | Resistor | No |  |
| C304 | TBD C / DNP | Capacitor | Yes |  |
| ANT2 | RF CONNECTOR TBD | RF connector | No | NOT RELEASED: no pin-bearing symbol; U.FL/MHF4 exact part and land pattern not selected |
| C305 | TBD C / DNP | Capacitor | Yes |  |
| R303 | 0R | Resistor | No |  |
| C306 | TBD C / DNP | Capacitor | Yes |  |
| ANT3 | RF CONNECTOR TBD | RF connector | No | NOT RELEASED: no pin-bearing symbol; U.FL/MHF4 exact part and land pattern not selected |
| C307 | TBD C / DNP | Capacitor | Yes |  |
| R304 | 0R | Resistor | No |  |
| C308 | TBD C / DNP | Capacitor | Yes |  |
| ANT4 | RF CONNECTOR TBD | RF connector | No | NOT RELEASED: no pin-bearing symbol; U.FL/MHF4 exact part and land pattern not selected |
| C321 | 220u low ESR | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C322 | 220u low ESR | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C323 | 22u | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C324 | 22u | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C325 | 22u | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C326 | 22u | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C327 | 1u | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C328 | 1u | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C329 | 100n | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| C330 | 100n | Capacitor | No | PROVISIONAL user target; revise to SIM8230C HDG and fit check |
| U3 | BMI270 | IC | No | I2C address 0x68; unused auxiliary pins DNC per table22; Electrical draft; land-pattern release pending |
| U4 | RV-3028-C7 | IC | No | Backup disabled by 10k to GND; keeps time with system power, not battery removal; Electrical draft; land-pattern release pending |
| C401 | 100n VDDIO | Capacitor | No |  |
| C402 | 100n VDD | Capacitor | No |  |
| C403 | 1u local | Capacitor | No |  |
| C404 | 100n RTC | Capacitor | No |  |
| R401 | 10k | Resistor | No |  |
| R402 | 10k | Resistor | No |  |
| J3 | J_LCD_GENERIC | LCD connector | No | NOT RELEASED: no pin-bearing symbol; LCD CONNECTOR PINOUT TBD; touch nets not connected to MCU |
| U13 | LCD backlight driver TBD | Backlight driver | No | Select after LED string voltage/current; no pin-bearing symbol |
| U9 | ES8311 | IC | No | NOT RELEASED: no pin-bearing symbol; Official source inaccessible; full datasheet, bias, decoupling and package required |
| MIC1 | TBD_MIC bottom-port | Analog MEMS microphone | No | NOT RELEASED: no pin-bearing symbol; Acoustic hole and recommended land pattern blocked |
| U10 | PAM8302A package TBD | IC | No | NOT RELEASED: no pin-bearing symbol; Model family known; package and gain/AC coupling/power domain not selected |
| J4 | SPEAKER CONTACTS | Connector | No | NOT RELEASED: no pin-bearing symbol; Floating BTL output; neither contact goes to GND |
| U11 | DRV2605LDGSR | IC | No | Motor selection/calibration TBD; enable uses removable pull-up, not spare MCU GPIO; Electrical draft; land-pattern release pending |
| J6 | MOTOR CONNECTOR | Connector | No | NOT RELEASED: no pin-bearing symbol; LRA/ERM voltage/current and actual connector required |
| C701 | 1u | Capacitor | No |  |
| C702 | 1u | Capacitor | No |  |
| C703 | 100n | Capacitor | No |  |
| R701 | 10k | Resistor | No |  |
| SW1 | SOS NO | Switch | No | Logical contacts only; physical switch footprint/pin map TBD |
| R711 | 1k | Resistor | No |  |
| R712 | 10k | Resistor | No |  |
| C711 | 100n | Capacitor | No |  |
| SW2 | AI NO | Switch | No | Logical contacts only; physical switch footprint/pin map TBD |
| R713 | 1k | Resistor | No |  |
| R714 | 10k | Resistor | No |  |
| C712 | 100n | Capacitor | No |  |
| J1 | POGO_4_LOGICAL | Connector | No | Numbering is user-defined. UART at connector has series resistors.; Electrical draft; land-pattern release pending |
| R801 | 1k | Resistor | No |  |
| R802 | 1k | Resistor | No |  |
| D3 | POGO UART ESD | ESD | No | NOT RELEASED: no pin-bearing symbol; Select clamps compatible with 3V3 factory UART |
| TP1 | TP_5V | Test point | No | Fixture name TP_5V; net VBUS_5V |
| TP2 | TP_VBAT | Test point | No | Fixture name TP_VBAT; net VBAT |
| TP3 | TP_VBAT_MODEM | Test point | No | Fixture name TP_VBAT_MODEM; net VBAT_MODEM |
| TP4 | TP_3V3 | Test point | No | Fixture name TP_3V3; net +3V3_SYS |
| TP5 | TP_1V8 | Test point | No | Fixture name TP_1V8; net +1V8 |
| TP6 | TP_GND | Test point | No | Fixture name TP_GND; net GND |
| TP7 | TP_UART_TX | Test point | No | Fixture name TP_UART_TX; net UART0_TX |
| TP8 | TP_UART_RX | Test point | No | Fixture name TP_UART_RX; net UART0_RX |
| TP9 | TP_I2C_SCL | Test point | No | Fixture name TP_I2C_SCL; net I2C_SCL |
| TP10 | TP_I2C_SDA | Test point | No | Fixture name TP_I2C_SDA; net I2C_SDA |
| TP11 | TP_MODEM_TX | Test point | No | Fixture name TP_MODEM_TX; net MODEM_TX |
| TP12 | TP_MODEM_RX | Test point | No | Fixture name TP_MODEM_RX; net MODEM_RX |
| TP13 | TP_MODEM_PWRKEY | Test point | No | Fixture name TP_MODEM_PWRKEY; net MODEM_PWRKEY |
| TP14 | TP_ESP_USB_DP | Test point | No | Fixture name TP_ESP_USB_DP; net ESP_USB_DP |
| TP15 | TP_ESP_USB_DM | Test point | No | Fixture name TP_ESP_USB_DM; net ESP_USB_DM |
| TP16 | TP_MODEM_USB_DP | Test point | No | Fixture name TP_MODEM_USB_DP; net MODEM_USB_DP |
| TP17 | TP_MODEM_USB_DM | Test point | No | Fixture name TP_MODEM_USB_DM; net MODEM_USB_DM |
| TP18 | TP_RESET | Test point | No | Fixture name TP_RESET; net ESP_EN |
| TP19 | TP_BOOT | Test point | No | Fixture name TP_BOOT; net ESP_BOOT |
| TP20 | TP_CHG_STATUS | Test point | No | Fixture name TP_CHG_STATUS; net CHG_STATUS |
| TP21 | TP_PGOOD | Test point | No | Fixture name TP_PGOOD; net PGOOD |
| D4 | USB ESD TBD | ESD | No | Required protection for ESP_USB_DP, ESP_USB_DM, GND; no pin-bearing symbol until selected |
| D5 | USB ESD TBD | ESD | No | Required protection for MODEM_USB_DP, MODEM_USB_DM, GND; no pin-bearing symbol until selected |
| NTC1 | 10k NTC in battery pack | Thermistor | No | Off-board actual cell temperature sensing; B curve and thresholds TBD |
| FB1 | Audio ferrite bead option | Ferrite bead | Yes | Not connected until codec power circuit confirmed; impedance/current TBD |
| ESIM1 | eSIM option | eSIM | Yes | Logical future option only; no shared populated SIM stubs or guessed pin map |
