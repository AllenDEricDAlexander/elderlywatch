# 网络矩阵 — 含未实现的接口意图

TBD 端点不是器件引脚。当前原生网表见 aiot-watch.net.xml；check_kicad.py 对所有已连接实际引脚比对网名。未知图框不会因此变成 IC。06_AUDIO 的 U9/U10 及 C601–C614/R601 已改为真实引脚端点；麦克风、扬声器、模组和显示接口仍按图框意图保留 TBD。

| Net | Endpoints | Status |
|---|---|---|
| +1V8 | U8.5; C112.1; TP5.1 | Draft connected terminals |
| +3V3_SYS | U7.7; U7.8; U8.1; U8.3; R103.1; R104.1; R105.1; R107.1; C108.1; C109.1; C110.1; C111.1; R108.1; U1.2; U1.3; U1.20; U1.46; U1.55; U1.56; R201.1; R202.1; R203.1; R204.1; C202.1; C203.1; C204.1; C205.1; C206.1; C207.1; C208.1; U3.5; U3.8; U3.12; U4.7; C401.1; C402.1; C403.1; C404.1; R401.1; J3.TBD; U9.3; U9.4; U9.11; C601.1; C602.1; C603.1; C604.1; U11.6; U11.10; C702.1; C703.1; R701.1; R712.1; R714.1; TP4.1 | HAS TBD ENDPOINTS |
| AMP_IN_N | U10.4; C611.2 | Draft connected terminals |
| AMP_IN_P | U10.3; C610.2 | Draft connected terminals |
| AMP_SD | U10.1; C614.1; R601.2 | Draft connected terminals |
| AUDIO_MCLK | U1.24; U9.2 | Draft connected terminals |
| BAT_ALERT | U5.5; R108.2; U1.14 | Draft connected terminals |
| BAT_NTC | U6.1; J5.TBD | HAS TBD ENDPOINTS |
| BTN_AI | U1.7; R713.2; R714.2; C712.1 | Draft connected terminals |
| BTN_AI_CONTACT | SW2.1; R713.1 | Draft connected terminals |
| BTN_SOS | U1.6; R711.2; R712.2; C711.1 | Draft connected terminals |
| BTN_SOS_CONTACT | SW1.1; R711.1 | Draft connected terminals |
| CELL_DIV_RF | U2.TBD; C303.1; R302.1 | HAS TBD ENDPOINTS |
| CELL_MAIN_RF | U2.TBD; C301.1; R301.1 | HAS TBD ENDPOINTS |
| CHG_ILIM | U6.12; R102.1 | Draft connected terminals |
| CHG_ISET | U6.16; R101.1 | Draft connected terminals |
| CHG_STATUS | U6.9; R103.2; TP20.1 | Draft connected terminals |
| CODEC_ADCVREF | U9.15; C606.1 | Draft connected terminals |
| CODEC_DACVREF | U9.14; C605.1 | Draft connected terminals |
| CODEC_DAC_N | U9.13; C611.1 | Draft connected terminals |
| CODEC_DAC_P | U9.12; C610.1 | Draft connected terminals |
| CODEC_MIC_N | U9.17; C609.2 | Draft connected terminals |
| CODEC_MIC_P | U9.18; C608.2 | Draft connected terminals |
| CODEC_VMID | U9.16; C607.1 | Draft connected terminals |
| DCDC_CTRL | U7.1; U7.14; R109.2 | Draft connected terminals |
| DCDC_FB | U7.5; R105.2; R106.1 | Draft connected terminals |
| DCDC_L1 | U7.11; L101.1 | Draft connected terminals |
| DCDC_L2 | U7.9; L101.2 | Draft connected terminals |
| DCDC_PG | U7.2; R107.2 | Draft connected terminals |
| DCDC_VAUX | U7.3; C104.1 | Draft connected terminals |
| ESP_BOOT | U1.5; R202.2; TP19.1 | Draft connected terminals |
| ESP_EN | U1.4; R201.2; C201.1; TP18.1 | Draft connected terminals |
| ESP_RF | U1.1; C307.1; R304.1 | Draft connected terminals |
| ESP_USB_DM | R206.2; TP15.1 | Draft connected terminals |
| ESP_USB_DM_RAW | U1.25; R206.1 | Draft connected terminals |
| ESP_USB_DP | R205.2; TP14.1 | Draft connected terminals |
| ESP_USB_DP_RAW | U1.26; R205.1 | Draft connected terminals |
| GND | U6.4; U6.6; U6.8; U6.EP; U7.4; U7.10; U7.15; U8.2; U5.1; U5.4; U5.6; U5.EP; J5.TBD; D1.TBD; R101.2; R102.2; C101.2; C102.2; C103.2; R106.2; C104.2; C105.2; C106.2; C107.2; C108.2; C109.2; C110.2; C111.2; C112.2; C113.2; U1.57; C201.2; C202.2; C203.2; C204.2; C205.2; C206.2; C207.2; C208.2; U2.TBD; J2.TBD; D2.TBD; C301.2; C302.2; ANT1.TBD; C303.2; C304.2; ANT2.TBD; C305.2; C306.2; ANT3.TBD; C307.2; C308.2; ANT4.TBD; C321.2; C322.2; C323.2; C324.2; C325.2; C326.2; C327.2; C328.2; C329.2; C330.2; U3.1; U3.6; U3.7; U4.5; U4.8; C401.2; C402.2; C403.2; C404.2; R402.2; J3.TBD; MIC1.TBD; U9.5; U9.10; U9.20; U10.7; C601.2; C602.2; C603.2; C604.2; C605.2; C606.2; C607.2; C612.2; C613.2; C614.2; U11.4; U11.8; C701.2; C702.2; C703.2; SW1.2; C711.2; SW2.2; C712.2; J1.2; D3.TBD; TP6.1 | HAS TBD ENDPOINTS |
| GNSS_RF | U2.TBD; C305.1; R303.1 | HAS TBD ENDPOINTS |
| HAPTIC_EN | U11.5; R701.2 | Draft connected terminals |
| HAPTIC_N | U11.9; J6.TBD | HAS TBD ENDPOINTS |
| HAPTIC_P | U11.7; J6.TBD | HAS TBD ENDPOINTS |
| HAPTIC_REG | U11.1; C701.1 | Draft connected terminals |
| I2C_SCL | U5.7; U1.10; R203.2; U3.13; U4.3; U9.1; U11.2; TP9.1 | Draft connected terminals |
| I2C_SDA | U5.8; U1.9; R204.2; U3.14; U4.4; U9.19; U11.3; TP10.1 | Draft connected terminals |
| I2S0_BCLK | U1.19; U9.6 | Draft connected terminals |
| I2S0_DIN | U1.23; U9.7 | Draft connected terminals |
| I2S0_DOUT | U1.22; U9.9 | Draft connected terminals |
| I2S0_LRCK | U1.21; U9.8 | Draft connected terminals |
| IMU_INT1 | U1.11; U3.4 | Draft connected terminals |
| IMU_INT2 | U1.12; U3.9 | Draft connected terminals |
| LCD_BL | U1.37; J3.TBD | HAS TBD ENDPOINTS |
| LCD_CS | U1.15; J3.TBD | HAS TBD ENDPOINTS |
| LCD_DC | U1.18; J3.TBD | HAS TBD ENDPOINTS |
| LCD_MOSI | U1.16; J3.TBD | HAS TBD ENDPOINTS |
| LCD_RST | U1.36; J3.TBD | HAS TBD ENDPOINTS |
| LCD_SCLK | U1.17; J3.TBD | HAS TBD ENDPOINTS |
| MCU_MODEM_RX | U1.43; U12.TBD | HAS TBD ENDPOINTS |
| MCU_MODEM_TX | U1.27; U12.TBD | HAS TBD ENDPOINTS |
| MCU_PCM_CLK | U1.44; U12.TBD | HAS TBD ENDPOINTS |
| MCU_PCM_DIN | U1.47; U12.TBD | HAS TBD ENDPOINTS |
| MCU_PCM_DOUT | U1.48; U12.TBD | HAS TBD ENDPOINTS |
| MCU_PCM_SYNC | U1.45; U12.TBD | HAS TBD ENDPOINTS |
| MIC1_N | C609.1; MIC1.TBD | HAS TBD ENDPOINTS |
| MIC1_P | MIC1.TBD; C608.1 | HAS TBD ENDPOINTS |
| MIC_SUPPLY_TBD | MIC1.TBD | HAS TBD ENDPOINTS |
| MODEM_PCM_CLK | U2.TBD; U12.TBD | HAS TBD ENDPOINTS |
| MODEM_PCM_DIN | U2.TBD; U12.TBD | HAS TBD ENDPOINTS |
| MODEM_PCM_DOUT | U2.TBD; U12.TBD | HAS TBD ENDPOINTS |
| MODEM_PCM_SYNC | U2.TBD; U12.TBD | HAS TBD ENDPOINTS |
| MODEM_PWRKEY | U2.TBD; TP13.1 | HAS TBD ENDPOINTS |
| MODEM_RESET | U2.TBD | HAS TBD ENDPOINTS |
| MODEM_RX | U2.TBD; U12.TBD; TP12.1 | HAS TBD ENDPOINTS |
| MODEM_STATUS | U2.TBD | HAS TBD ENDPOINTS |
| MODEM_TX | U2.TBD; U12.TBD; TP11.1 | HAS TBD ENDPOINTS |
| MODEM_USB_DM | U2.TBD; TP17.1 | HAS TBD ENDPOINTS |
| MODEM_USB_DP | U2.TBD; TP16.1 | HAS TBD ENDPOINTS |
| PGOOD | U6.7; R104.2; TP21.1 | Draft connected terminals |
| POGO_UART_RX | J1.4; R802.1; D3.TBD | HAS TBD ENDPOINTS |
| POGO_UART_TX | J1.3; R801.2; D3.TBD | HAS TBD ENDPOINTS |
| RF_CELL_DIV | R302.2; C304.1; ANT2.TBD | HAS TBD ENDPOINTS |
| RF_CELL_MAIN | R301.2; C302.1; ANT1.TBD | HAS TBD ENDPOINTS |
| RF_GNSS | R303.2; C306.1; ANT3.TBD | HAS TBD ENDPOINTS |
| RF_WIFI | R304.2; C308.1; ANT4.TBD | HAS TBD ENDPOINTS |
| RTC_INT | U1.13; U4.2; R401.2 | Draft connected terminals |
| RTC_VBACKUP | U4.6; R402.1 | Draft connected terminals |
| SIM_CLK | U2.TBD; J2.TBD; D2.TBD | HAS TBD ENDPOINTS |
| SIM_DATA | U2.TBD; J2.TBD; D2.TBD | HAS TBD ENDPOINTS |
| SIM_RST | U2.TBD; J2.TBD; D2.TBD | HAS TBD ENDPOINTS |
| SIM_VCC | U2.TBD; J2.TBD; D2.TBD | HAS TBD ENDPOINTS |
| SPK_N | J4.TBD; U10.8 | HAS TBD ENDPOINTS |
| SPK_P | J4.TBD; U10.5 | HAS TBD ENDPOINTS |
| SYS | U6.5; U6.10; U6.11; U7.12; U7.13; C103.1; C105.1; C106.1; C107.1; R109.1 | Draft connected terminals |
| TP_INT | J3.TBD | HAS TBD ENDPOINTS |
| TP_SCL | J3.TBD | HAS TBD ENDPOINTS |
| TP_SDA | J3.TBD | HAS TBD ENDPOINTS |
| UART0_RX | U1.50; R802.2; TP8.1 | Draft connected terminals |
| UART0_TX | U1.49; R801.1; TP7.1 | Draft connected terminals |
| VBAT | U6.2; U6.3; U5.2; U5.3; J5.TBD; C102.1; C113.1; U10.6; C612.1; C613.1; R601.1; TP2.1 | HAS TBD ENDPOINTS |
| VBAT_MODEM | U2.TBD; C321.1; C322.1; C323.1; C324.1; C325.1; C326.1; C327.1; C328.1; C329.1; C330.1; TP3.1 | HAS TBD ENDPOINTS |
| VBUS_5V | U6.13; D1.TBD; C101.1; J1.1; TP1.1 | HAS TBD ENDPOINTS |
