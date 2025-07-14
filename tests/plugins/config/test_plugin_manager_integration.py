# -*- coding: utf-8 -*-
"""
插件管理器配置验证集成测试

测试E8修复：插件管理器强制配置验证功能
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from simtradelab.backtest.plugins.config import SimpleMatchingEngineConfig
from simtradelab.core.plugin_manager import PluginLoadError, PluginManager
from simtradelab.plugins.base import BasePlugin, PluginMetadata
from simtradelab.plugins.data.config import MockDataPluginConfig


class MockTestPlugin(BasePlugin):
    """测试插件类"""

    METADATA = PluginMetadata(name="TestPlugin", version="1.0.0", description="测试插件")

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass


class MockTestPluginWithConfigModel(BasePlugin):
    """有配置模型的测试插件"""

    METADATA = PluginMetadata(
        name="TestPluginWithConfigModel", version="1.0.0", description="带配置模型的测试插件"
    )

    # E8修复：定义配置模型
    config_model = SimpleMatchingEngineConfig

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass


class TestPluginManagerConfigValidation:
    """插件管理器配置验证测试"""

    def test_load_plugin_without_config_model(self):
        """测试加载没有配置模型的插件"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册插件
        plugin_name = manager.register_plugin(MockTestPlugin)

        # 加载插件 - 应该成功（使用基础配置）
        instance = manager.load_plugin(plugin_name)

        assert instance is not None
        assert isinstance(instance, MockTestPlugin)
        assert manager.get_plugin(plugin_name) is not None

    def test_load_plugin_with_config_model_default_config(self):
        """测试使用默认配置加载有配置模型的插件"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册插件
        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)

        # 加载插件 - 应该使用默认配置成功
        instance = manager.load_plugin(plugin_name)

        assert instance is not None
        assert isinstance(instance, MockTestPluginWithConfigModel)
        assert manager.get_plugin(plugin_name) is not None

    def test_load_plugin_with_valid_config_object(self):
        """测试使用有效配置对象加载插件"""
        manager = PluginManager(auto_register_builtin=False)

        # 创建有效配置
        config = SimpleMatchingEngineConfig(
            price_tolerance=Decimal("0.02"), enable_partial_fill=True
        )

        # 注册并加载插件
        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel, config)
        instance = manager.load_plugin(plugin_name)

        assert instance is not None
        assert isinstance(instance, MockTestPluginWithConfigModel)

    def test_load_plugin_with_valid_config_dict(self):
        """测试使用有效配置字典加载插件"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册插件
        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)

        # 使用字典配置加载插件
        config_dict = {
            "price_tolerance": "0.03",
            "enable_partial_fill": False,
            "max_order_size": "5000",
        }

        instance = manager.load_plugin(plugin_name, config_dict)

        assert instance is not None
        assert isinstance(instance, MockTestPluginWithConfigModel)

    def test_load_plugin_with_invalid_config_dict(self):
        """测试使用无效配置字典加载插件"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册插件
        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)

        # 使用无效字典配置加载插件
        invalid_config_dict = {
            "price_tolerance": "2.0",  # 大于最大值1.0
            "enable_partial_fill": "invalid_bool",
        }

        with pytest.raises(PluginLoadError):
            manager.load_plugin(plugin_name, invalid_config_dict)

    @patch(
        "simtradelab.core.plugin_manager.PluginManager._register_core_plugins",
        MagicMock(return_value=None),
    )
    @patch("simtradelab.core.plugin_manager.get_config_manager")
    def test_load_plugin_with_wrong_config_type(self, mock_get_config_manager, *args):
        """
        测试场景：加载插件时传入一个不兼容的配置对象。
        预期行为：ConfigManager应抛出验证错误，PluginManager将其包装为PluginLoadError。
        """
        # 1. 准备
        # 模拟ConfigManager在验证时抛出ValidationError
        mock_config_manager = MagicMock()
        mock_get_config_manager.return_value = mock_config_manager
        validation_error = ValidationError.from_exception_data(
            title="SimpleMatchingEngineConfig", line_errors=[]
        )
        mock_config_manager.create_validated_config.side_effect = validation_error

        # 2. 执行
        # @patch确保了在实例化PluginManager时，_register_core_plugins已经被模拟
        manager = PluginManager()
        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)
        wrong_config_object = MockDataPluginConfig()

        # 3. 断言
        with pytest.raises(PluginLoadError) as excinfo:
            manager.load_plugin(plugin_name, wrong_config_object)

        # 验证原始错误是ValidationError
        assert isinstance(excinfo.value.__cause__, ValidationError)

        # 验证ConfigManager被正确调用
        mock_config_manager.create_validated_config.assert_called_once_with(
            MockTestPluginWithConfigModel, wrong_config_object
        )

    def test_config_conversion_from_dict(self):
        """测试从字典配置转换"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册插件
        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)

        # 使用字典配置
        config_dict = {
            "price_tolerance": "0.05",
            "enable_partial_fill": True,
            "max_order_size": "8000",
        }

        instance = manager.load_plugin(plugin_name, config_dict)

        # 验证配置已正确转换和应用
        assert instance is not None
        # 注意：这里需要插件实际保存配置才能验证

    def test_config_conversion_from_pydantic_model(self):
        """测试从Pydantic模型转换"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册插件
        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)

        # 使用不同但兼容的Pydantic配置模型
        from simtradelab.plugins.config.base_config import BasePluginConfig

        base_config = BasePluginConfig()

        # 插件管理器应该尝试转换配置
        instance = manager.load_plugin(plugin_name, base_config)

        assert instance is not None

    def test_plugin_already_loaded_error(self):
        """测试插件已加载错误"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册并加载插件
        plugin_name = manager.register_plugin(MockTestPlugin)
        manager.load_plugin(plugin_name)

        # 尝试再次加载应该失败
        with pytest.raises(PluginLoadError, match="already loaded"):
            manager.load_plugin(plugin_name)

    def test_plugin_not_registered_error(self):
        """测试插件未注册错误"""
        manager = PluginManager(auto_register_builtin=False)

        # 尝试加载未注册的插件
        with pytest.raises(PluginLoadError, match="not registered"):
            manager.load_plugin("NonExistentPlugin")

    def test_config_validation_logging(self):
        """测试配置验证日志"""
        with patch("logging.getLogger") as mock_logger:
            manager = PluginManager(auto_register_builtin=False)

            # 注册插件
            plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)

            # 加载插件
            manager.load_plugin(plugin_name)

            # 验证日志记录
            logger_instance = mock_logger.return_value
            logger_instance.info.assert_called()

    def test_reload_plugin_config_validation(self):
        """测试重载插件时的配置验证"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册并加载插件
        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)
        manager.load_plugin(plugin_name)

        # 重载插件
        result = manager.reload_plugin(plugin_name)

        assert result is True
        assert manager.get_plugin(plugin_name) is not None

    def test_batch_load_with_config_validation(self):
        """测试批量加载插件时的配置验证"""
        manager = PluginManager(auto_register_builtin=False)

        # 注册多个插件
        plugin1_name = manager.register_plugin(MockTestPlugin)
        plugin2_name = manager.register_plugin(MockTestPluginWithConfigModel)

        # 批量加载
        results = manager.load_all_plugins(start=False)

        assert results[plugin1_name] is True
        assert results[plugin2_name] is True

        # 验证插件已加载
        assert manager.get_plugin(plugin1_name) is not None
        assert manager.get_plugin(plugin2_name) is not None


class TestConfigValidationEdgeCases:
    """配置验证边界情况测试"""

    def test_config_model_none(self):
        """测试插件的配置模型为None"""

        class PluginWithNoneConfigModel(BasePlugin):
            METADATA = PluginMetadata(
                name="PluginWithNoneConfigModel",
                version="1.0.0",
                description="配置模型为None的插件",
            )

            config_model = None  # 显式设置为None

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        manager = PluginManager(auto_register_builtin=False)
        plugin_name = manager.register_plugin(PluginWithNoneConfigModel)

        # 应该使用基础配置成功加载
        instance = manager.load_plugin(plugin_name)
        assert instance is not None

    def test_config_model_not_pydantic(self):
        """测试插件的配置模型不是Pydantic类"""

        class NonPydanticConfig:
            pass

        class PluginWithInvalidConfigModel(BasePlugin):
            METADATA = PluginMetadata(
                name="PluginWithInvalidConfigModel",
                version="1.0.0",
                description="无效配置模型的插件",
            )

            config_model = NonPydanticConfig

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        manager = PluginManager(auto_register_builtin=False)
        plugin_name = manager.register_plugin(PluginWithInvalidConfigModel)

        # 应该处理错误情况
        with pytest.raises(PluginLoadError):
            manager.load_plugin(plugin_name)

    def test_empty_config_dict(self):
        """测试空配置字典"""
        manager = PluginManager(auto_register_builtin=False)

        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)

        # 使用空字典
        instance = manager.load_plugin(plugin_name, {})

        assert instance is not None

    def test_config_with_extra_fields(self):
        """测试包含额外字段的配置"""
        manager = PluginManager(auto_register_builtin=False)

        plugin_name = manager.register_plugin(MockTestPluginWithConfigModel)

        # 包含额外字段的配置
        config_dict = {
            "price_tolerance": "0.02",
            "enable_partial_fill": True,
            "unknown_field": "should_be_ignored",  # 额外字段
        }

        # 应该忽略额外字段并成功加载
        instance = manager.load_plugin(plugin_name, config_dict)
        assert instance is not None

    def teardown_method(self):
        """清理测试环境"""
        # 确保每个测试后清理插件管理器
        pass
