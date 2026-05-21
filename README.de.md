# 📈 SimTradeLab

[English](README.md) | [中文](README.zh-CN.md) | Deutsch

**Leichtgewichtiges quantitatives Backtesting-Framework — Lokale PTrade-API-Simulation**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![License: Commercial](https://img.shields.io/badge/License-Commercial--Available-red)](licenses/LICENSE-COMMERCIAL.md)
[![Version](https://img.shields.io/badge/Version-2.12.0-orange.svg)](#)
[![PyPI](https://img.shields.io/pypi/v/simtradelab.svg)](https://pypi.org/project/simtradelab/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/simtradelab.svg)](https://pypi.org/project/simtradelab/)

> Vollständige PTrade-API-Simulation — Strategien laufen nahtlos zwischen SimTradeLab und PTrade. Siehe auch: [ptradeAPI](https://github.com/kay-ou/ptradeAPI)

---

## 🎯 Warum SimTradeLab?

| | SimTradeLab | PTrade |
|---|---|---|
| Geschwindigkeit | **100–160x schneller** | Referenz |
| Startzeit | Unter einer Sekunde (Daten bleiben im Speicher) | Minuten |
| API-Abdeckung | 46 Backtest-/Research-APIs | Vollplattform |
| Strategieportierung | Keine Codeänderungen | Keine Codeänderungen |
| Umgebung | Lokal, kostenlos, Open Source | Cloud, lizenziert |

**Kernfunktionen:**

- ✅ **62 APIs** — 100% Abdeckung für Aktien-Backtesting (Tages- und Minutenbalken)
- ⚡ **100–160x schneller** als die PTrade-Plattform
- 🚀 **In-Memory-Datenpersistenz** — Singleton-Muster, Start unter einer Sekunde nach dem ersten Laden
- 💾 **Mehrstufiges Caching** — LRU-Caches für MA/VWAP/Anpassungsfaktoren/Historie, >95% Trefferquote
- 🧠 **Intelligentes Datenladen** — AST-Analyse des Strategiecodes, lädt nur benötigte Daten
- 🔧 **Lebenszyklussteuerung** — 7 Lebenszyklusphasen, strikte Simulation der PTrade-API-Beschränkungen
- 📊 **Vollständige Statistikberichte** — Renditen, Risikokennzahlen (Sharpe/Sortino/Calmar), Handelsdetails, FIFO-Dividendensteuer, CSV-Export
- 🔌 **Multi-Markt** — Integrierte CN (A-Aktien) und US-Marktprofile mit automatischer Handelsregelanpassung
- 🌐 **i18n** — Backtest-Ausgabe auf Chinesisch, Englisch oder Deutsch

---

## 🚀 Mehr gewünscht? Probieren Sie SimTradeDesk

> **[SimTradeDesk](https://github.com/kay-ou/SimTradeDesk)** ist eine professionelle Desktop-Anwendung auf Basis von SimTradeLab — keine Programmierung erforderlich.

| Funktion | SimTradeLab (dieses Repo) | SimTradeDesk |
|---|---|---|
| Zielgruppe | Entwickler & Quant-Ingenieure | Alle Trader |
| Oberfläche | Python-API | Desktop-GUI |
| Strategiebearbeitung | Code-Editor | Integrierter Editor mit Syntaxhervorhebung |
| Visualisierung | PNG-Charts | Interaktive Echtzeit-Charts |
| Datenverwaltung | Manuelle Einrichtung | Ein-Klick-Download & Update |
| Parameteroptimierung | Code schreiben | Visueller Optimierer |

**[👉 SimTradeDesk herunterladen →](https://github.com/kay-ou/SimTradeDesk)**

---

## 📦 Schnellstart

```bash
pip install simtradelab

# Optional: Technische Indikatoren (erfordert System-ta-lib)
pip install simtradelab[indicators]

# Optional: Parameteroptimierung
pip install simtradelab[optimizer]
```

**Daten:** Verwenden Sie [SimTradeData](https://github.com/kay-ou/SimTradeData) zum Download historischer Daten für chinesische A-Aktien und US-Aktien.

**Backtest ausführen:**

```python
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig

config = BacktestConfig(
    # --- Pflichtfelder ---
    strategy_name='my_strategy',       # Strategieordner unter strategies/
    start_date='2024-01-01',           # Backtest-Startdatum
    end_date='2024-12-31',             # Backtest-Enddatum

    # --- Kapital & Markt ---
    initial_capital=100000.0,          # Startkapital (muss > 0 sein)
    market='CN',                       # Markt: 'CN' (A-Aktien) | 'US'
    broker_profile='auto',             # Broker-API-Profil: 'auto' | 'guosheng' | 'dongguan' | 'shanxi'
    t_plus_1=None,                     # T+1-Override: None=Marktstandard (CN=True, US=False)
    benchmark_code='',                 # Benchmark-Code, leer=Marktstandard

    # --- Frequenz ---
    frequency='1d',                    # Balkenfrequenz: '1d' (täglich) | '1m' (Minute)

    # --- Pfade ---
    data_path='~/.simtradelab/data',   # Marktdatenverzeichnis
    strategies_path='./strategies',    # Strategien-Stammverzeichnis

    # --- Leistung ---
    enable_multiprocessing=True,       # Paralleles Datenladen aktivieren
    num_workers=None,                  # Anzahl Worker (None=auto, muss >= 1 sein)
    use_data_server=True,              # In-Memory-Datenserver verwenden (Singleton)

    # --- Ausgabe ---
    enable_charts=True,                # PNG-Chart generieren
    enable_logging=True,               # Logdatei schreiben
    enable_export=False,               # Handelsdetails als CSV exportieren

    # --- i18n ---
    locale='auto',                     # Log-Sprache: 'zh' | 'en' | 'de' (auto: CN-Markt→zh, sonst Systemsprache)
    optimization_mode=False,           # Optimierungsmodus (vom Optimierer gesteuert)

    # --- Einstiegsdatei ---
    strategy_file='backtest.py',       # Einstiegsdatei: 'backtest.py' | 'live.py'
)
runner = BacktestRunner()
report = runner.run(config=config)
```

---

## 📚 API-Übersicht

46 Backtest-/Research-APIs — 100% Abdeckung für Aktien-Backtesting.

| Kategorie | APIs |
|-----------|------|
| Handel | order, order_target, order_value, order_target_value, cancel_order, get_positions, get_trades |
| Daten | get_price, get_history, get_fundamentals, get_stock_info |
| Sektoren | get_index_stocks, get_industry_stocks, get_stock_blocks |
| Indikatoren | get_MACD, get_KDJ, get_RSI, get_CCI |
| Konfiguration | set_benchmark, set_commission, set_slippage, set_universe, set_parameters |
| Lebenszyklus | initialize, before_trading_start, handle_data, after_trading_end |

---

## 📄 Lizenz

**Doppellizenz**-Modell:

- **AGPL-3.0** — Kostenlos für Open-Source-Projekte und persönliche Forschung. Siehe [LICENSE](LICENSE)
- **Kommerzielle Lizenz** — Für Closed-Source / kommerzielle Nutzung. Siehe [LICENSE-COMMERCIAL.md](licenses/LICENSE-COMMERCIAL.md) oder kontaktieren Sie [kayou@duck.com](mailto:kayou@duck.com)

---

## 🤝 Mitwirken

- 🐛 [Fehler melden](https://github.com/kay-ou/SimTradeLab/issues)
- 💻 Fehlende API-Funktionen implementieren
- 📚 Dokumentation verbessern

Siehe [CONTRIBUTING.md](docs/CONTRIBUTING.md) für CLA-Details.

---

## ⚖️ Haftungsausschluss

SimTradeLab ist ein von der Community entwickeltes Open-Source-Backtesting-Framework, inspiriert vom ereignisgesteuerten Design von PTrade. Es enthält keinen Quellcode, keine Marken oder geschützte Inhalte von PTrade. Dieses Projekt ist weder mit PTrade verbunden noch von PTrade unterstützt. Benutzer sind für die Einhaltung lokaler Vorschriften und Plattformbedingungen verantwortlich.

---

<div align="center">

**⭐ Wenn dieses Projekt Ihnen hilft, geben Sie uns einen Stern!**

[🐛 Fehler melden](https://github.com/kay-ou/SimTradeLab/issues) | [💡 Feature-Anfrage](https://github.com/kay-ou/SimTradeLab/issues) | [🖥️ SimTradeDesk](https://github.com/kay-ou/SimTradeDesk)

---

## 💖 Sponsoring

Wenn dieses Projekt Ihnen hilft, erwägen Sie eine Spende!

<img src="docs/sponsor/WechatPay.png?raw=true" alt="WeChat Pay" width="200">
<img src="docs/sponsor/AliPay.png?raw=true" alt="Alipay" width="200">

</div>
