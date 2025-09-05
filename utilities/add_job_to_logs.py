import logging

from celery import signals


@signals.after_setup_task_logger.connect
def setup_celery_file_logging(logger, **kwargs):
    """Add rotating file logs to celery global logger."""
    celery_log_file_handler = logging.handlers.RotatingFileHandler(
        filename="/opt/nautobot/logs/debug.log", maxBytes=15728640
    )

    logger.addHandler(celery_log_file_handler)
