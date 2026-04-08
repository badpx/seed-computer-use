"""Discovery and loading for device plugins."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

from .base import DevicePluginSpec


def built_in_devices_dir() -> Path:
    return Path(__file__).resolve().parent / 'plugins'


def project_plugins_dir() -> Path:
    return Path(__file__).resolve().parents[2] / 'plugins'


def discover_device_plugins(
    search_dirs: Optional[Iterable[str]] = None,
) -> Dict[str, DevicePluginSpec]:
    specs: Dict[str, DevicePluginSpec] = {}
    paths = [built_in_devices_dir(), project_plugins_dir()]
    for directory in search_dirs or ():
        if not directory:
            continue
        paths.append(Path(directory).expanduser())

    for base_path in paths:
        if not base_path.exists():
            continue
        for child in sorted(base_path.iterdir()):
            if not child.is_dir():
                continue
            manifest_path = child / 'plugin.json'
            plugin_path = child / 'plugin.py'
            if not manifest_path.exists() or not plugin_path.exists():
                continue
            spec = _load_plugin_spec(manifest_path=manifest_path, plugin_path=plugin_path)
            specs[spec.name] = spec
    return specs


def load_plugin_factory(spec: DevicePluginSpec) -> Callable:
    package_name = _ensure_plugin_package_namespace(spec)
    module_name = f'{package_name}.plugin'
    module_spec = importlib.util.spec_from_file_location(module_name, spec.plugin_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f'无法加载设备插件模块: {spec.plugin_path}')
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    module_spec.loader.exec_module(module)

    module_name_part, _, attr_name = spec.entrypoint.partition(':')
    if module_name_part and module_name_part != 'plugin':
        alt_path = spec.directory / f'{module_name_part}.py'
        alt_spec = importlib.util.spec_from_file_location(
            f'{package_name}.{module_name_part}',
            alt_path,
        )
        if alt_spec is None or alt_spec.loader is None:
            raise RuntimeError(f'无法加载设备插件入口模块: {alt_path}')
        module = importlib.util.module_from_spec(alt_spec)
        sys.modules[f'{package_name}.{module_name_part}'] = module
        alt_spec.loader.exec_module(module)

    factory = getattr(module, attr_name or 'create_adapter', None)
    if factory is None or not callable(factory):
        raise RuntimeError(f'设备插件入口不可调用: {spec.entrypoint}')
    return factory


def _ensure_plugin_package_namespace(spec: DevicePluginSpec) -> str:
    package_name = f'computer_use.devices.plugins.{spec.directory.name}'
    package = sys.modules.get(package_name)
    if package is None:
        package = types.ModuleType(package_name)
        package.__file__ = str(spec.directory / '__init__.py')
        package.__path__ = [str(spec.directory)]
        package.__package__ = package_name
        sys.modules[package_name] = package
    else:
        package.__path__ = [str(spec.directory)]
    return package_name


def _load_plugin_spec(
    manifest_path: Path,
    plugin_path: Path,
) -> DevicePluginSpec:
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    name = str(payload.get('name') or '').strip()
    description = str(payload.get('description') or '').strip()
    entrypoint = str(payload.get('entrypoint') or '').strip()
    if not name or not description or not entrypoint:
        raise RuntimeError(f'设备插件清单缺少必要字段: {manifest_path}')
    return DevicePluginSpec(
        name=name,
        description=description,
        entrypoint=entrypoint,
        directory=manifest_path.parent,
        plugin_path=plugin_path,
        manifest_path=manifest_path,
        metadata={
            key: value
            for key, value in payload.items()
            if key not in {'name', 'description', 'entrypoint'}
        },
    )
