import smtplib

_orig_starttls = smtplib.SMTP.starttls

def _patched_starttls(self, keyfile=None, certfile=None, context=None):
    if context is not None:
        return _orig_starttls(self, context=context)
    return _orig_starttls(self)

smtplib.SMTP.starttls = _patched_starttls

from .celery import app as celery_app

__all__ = ('celery_app',)
