import os
from pathlib import Path

from src.common.pipeline_health_monitor import PipelineHealthMonitor


def _prepare_zones(tmp_path: Path, monkeypatch) -> None:
    zone_defaults = {
        'LANDING_ZONE': '1_landing',
        'RAW_ZONE': '2_raw',
        'STAGING_ZONE': '3_staging',
    }
    for env_var, relative in zone_defaults.items():
        zone_dir = tmp_path / relative
        zone_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(env_var, relative)


def test_curated_freshness_uses_environment_paths(tmp_path, monkeypatch):
    _prepare_zones(tmp_path, monkeypatch)
    curated_dir = tmp_path / 'custom_curated'
    curated_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('CURATED_ZONE', 'custom_curated')

    curated_file = curated_dir / 'tiktok_analytics_curated_20251014_064846.csv'
    curated_file.write_text('artist,date\nA,2025-10-14\n', encoding='utf-8')

    monitor = PipelineHealthMonitor(
        enable_auto_remediation=False,
        enable_notifications=False,
        project_root=tmp_path,
    )

    freshness = monitor.check_zone_freshness('tiktok')
    curated_freshness = freshness['curated']

    assert curated_freshness['exists'] is True
    assert curated_freshness['latest_file'] == curated_file.name
    assert curated_freshness['full_path'] == str(curated_file.relative_to(tmp_path))
    assert curated_freshness['days_old'] == 0


def test_curated_freshness_supports_absolute_zone(tmp_path, monkeypatch):
    _prepare_zones(tmp_path, monkeypatch)

    absolute_curated = (tmp_path / 'absolute_curated').resolve()
    absolute_curated.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv('CURATED_ZONE', str(absolute_curated))

    output_file = absolute_curated / 'linktree_analytics.csv'
    output_file.write_text('date,views\n2025-10-14,5\n', encoding='utf-8')

    monitor = PipelineHealthMonitor(
        enable_auto_remediation=False,
        enable_notifications=False,
        project_root=tmp_path,
    )

    freshness = monitor.check_zone_freshness('linktree')
    curated_freshness = freshness['curated']

    assert curated_freshness['exists'] is True
    assert curated_freshness['latest_file'] == output_file.name
    assert curated_freshness['full_path'].endswith(output_file.name)
