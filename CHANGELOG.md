# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-07-05

### 🌟 Major Features Added

#### 🌐 Real Data Source Integration
- **AkShare Integration**: Added support for real A-share market data with live prices, volumes, and trading information
- **Tushare Integration**: Professional financial data interface support (requires token configuration)
- **Smart Data Source Management**: Automatic fallback to backup data sources when primary source fails
- **Configuration Management**: Unified data source configuration through `ptrade_config.yaml`

#### ⚡ Command Line Tool
- **Professional CLI**: New `ptradeSim.py` command-line tool for strategy execution
- **Rich Parameter Support**: Comprehensive parameter configuration including strategy files, data sources, securities, time ranges, and initial capital
- **Multiple Output Modes**: Verbose, quiet, and normal output modes for different use cases
- **Smart Validation**: Automatic parameter validation and user-friendly error messages

### 🛠️ Engine Optimizations

#### 🔧 Core Engine Improvements
- **API Injection Fix**: Resolved issue where class objects were incorrectly injected, ensuring only function objects are injected
- **set_commission Update**: New function signature `set_commission(commission_ratio=0.0003, min_commission=5.0, type="STOCK")`
- **Performance Analysis Enhancement**: Improved performance metrics calculation with better error handling for insufficient data
- **Strategy Compatibility**: Removed non-standard API functions (like `on_strategy_end`) to ensure full ptrade compatibility

#### 📊 Strategy Improvements
- **Real Data Strategy**: New `real_data_strategy.py` demonstrating real A-share data usage
- **Smart Fallback Mechanism**: Automatic switch to simple trading strategy when historical data is insufficient
- **Detailed Trading Logs**: Chinese language log output for better strategy debugging and analysis
- **Position Management**: Fixed position data format issues, supporting dictionary-format position information

### 🔧 Dependency Management
- **Modular Dependencies**: Moved data source dependencies to optional groups, supporting on-demand installation
- **Version Conflict Resolution**: Fixed akshare duplicate definition issues
- **Simplified Installation**: Support for `poetry install --with data` to install data source dependencies

### 📚 Documentation Updates
- **Comprehensive README**: Updated with v2.1.0 features, real data source usage, and command-line tool documentation
- **Usage Examples**: Added complete code examples for both CSV and real data sources
- **Parameter Reference**: Detailed parameter tables and usage scenarios
- **Quick Start Guide**: Streamlined onboarding process for new users

### 🧪 Testing Improvements
- **Real Data Testing**: Comprehensive testing with actual A-share data (Ping An Bank, Vanke A, SPDB)
- **CLI Tool Testing**: Full command-line interface testing with various parameter combinations
- **Error Handling**: Improved error messages and edge case handling

### 🔄 Breaking Changes
- **Command Line Tool**: Renamed from `run_strategy.py` to `ptradeSim.py` for better branding
- **Data Source Configuration**: Changed from `data_path=AkshareDataSource()` to `data_source=AkshareDataSource()`
- **Dependency Structure**: Data sources now require explicit installation with `--with data` flag

### 🐛 Bug Fixes
- Fixed position data access issues with real data sources
- Resolved historical data format inconsistencies
- Corrected API injection mechanism to prevent class object injection
- Fixed commission function signature compatibility

### 📈 Performance Improvements
- Optimized data loading for real data sources
- Improved memory usage for large datasets
- Enhanced error handling and recovery mechanisms

---

## [2.0.0] - 2024-12

### Added
- Multi-data source support (Tushare, AkShare, CSV)
- Configuration management through YAML files
- Smart fallback mechanisms for data sources
- Caching optimization for API calls
- Backward compatibility with existing CSV data sources

### Changed
- Enhanced data source architecture
- Improved error handling and logging
- Updated documentation structure

### Fixed
- Data loading performance issues
- API rate limiting problems
- Configuration file parsing errors

---

## [1.0.0] - 2024-11

### Added
- Initial release of ptradeSim
- Basic backtesting engine
- CSV data source support
- Strategy framework compatibility
- Performance analysis tools
- Basic documentation

### Features
- Strategy backtesting with historical data
- Portfolio management and tracking
- Performance metrics calculation
- Order execution simulation
- Risk management tools
