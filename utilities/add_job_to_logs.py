import logging
import logging.handlers

from celery import signals

LOG_PATH = "/var/log/jobs_logs.log"


def _make_file_handler() -> logging.Handler:
    """Create a rotating file handler with a formatter that will include tracebacks."""
    h = logging.handlers.RotatingFileHandler(
        filename=LOG_PATH,
        maxBytes=15 * 1024 * 1024,  # 15 MB
        backupCount=5,
        encoding="utf-8",
    )
    h.setLevel(logging.DEBUG)
    h.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
        )
    )
    return h


@signals.after_setup_logger.connect
def setup_celery_root_logging(logger: logging.Logger, **kwargs):
    """
    Add file handler to Celery's *global* logger so worker/internal errors
    (including tracebacks) are captured.
    """
    logger.addHandler(_make_file_handler())


@signals.after_setup_task_logger.connect
def setup_celery_task_logging(logger: logging.Logger, **kwargs):
    """
    Add file handler to task loggers (get_task_logger) so your task code logs
    end up in the same file.
    """
    logger.addHandler(_make_file_handler())


@signals.task_failure.connect
def log_task_failure(
    sender=None, task_id=None, exception=None, args=None, kwargs=None, einfo=None, **kw
):
    """
    Ensure tracebacks are written even if other logging config gets in the way.
    Celery passes `einfo` (ExceptionInfo) which contains the traceback.
    """
    log = logging.getLogger("celery.app.trace")
    # Use the provided exception info so the full traceback is emitted.
    exc_info = getattr(einfo, "exc_info", True)
    log.error(
        "Task failed: %s (task=%s id=%s args=%r kwargs=%r)",
        exception,
        getattr(sender, "name", sender),
        task_id,
        args,
        kwargs,
        exc_info=exc_info,
    )
