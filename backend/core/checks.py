from django.core.checks import Warning, Error, register, Tags
from pathlib import Path
from django.conf import settings

@register()
def check_locale_paths(app_configs, **kwargs):
    errors = []
    for p in getattr(settings, 'LOCALE_PATHS', []):
        if not Path(p).exists():
            errors.append(Error(
                f'LOCALE_PATHS entry does not exist: {p}',
                id='rivin.E001',
            ))
    return errors

@register(Tags.security, deploy=True)
def check_allowed_hosts(app_configs, **kwargs):
    warnings = []
    if not settings.DEBUG and '*' in settings.ALLOWED_HOSTS:
        warnings.append(Warning(
            'ALLOWED_HOSTS contains "*" while DEBUG=False — set explicit hosts in production.',
            id='rivin.W001',
        ))
    return warnings
