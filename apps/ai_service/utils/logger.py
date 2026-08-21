import logging
import os

import logfire


def setup_logger(use_long_path: bool = True):
    """
    Centralized configuration for standard Python Logging and Logfire.
    """
    # 1. Configure the native Logfire behavior (Dashboard telemetry)
    logfire.configure(
        send_to_logfire=False,
        # service_name sets the OTel resource name shown in the Jaeger "Service"
        # dropdown. Without it, traces land under "unknown_service". Override with
        # the OTEL_SERVICE_NAME env var if needed.
        service_name=os.getenv("OTEL_SERVICE_NAME", "ai-service"),
        # inspect_arguments=False — disables Logfire's f-string source introspection
        # (auto-capturing f-string vars as attributes). It fails under the uvicorn
        # reloader / .pyc-without-source and emits "Failed to introspect calling
        # code" warnings. We pass explicit kwargs to spans, so we don't need it.
        inspect_arguments=False,
        # Turn off native verbose console so standard logging can take over
        console=False,
        # pydantic_plugin=logfire.PydanticPlugin(record="all"),
    )

    # Select the path format based on the variable
    path_format = "%(pathname)s" if use_long_path else "%(filename)s"

    # Log level from env (LOG_LEVEL=DEBUG surfaces tool-level traces in tools/*.py).
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

    # 2. Configure standard Python logging for the local terminal AND Logfire dashboard
    logging.basicConfig(
        level=level,
        format=f"%(asctime)s.%(msecs)03d [{path_format}:%(lineno)d] %(funcName)s(): %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),  # Prints to terminal using your custom format
            logfire.LogfireLoggingHandler(),  # Intercepts and sends to Logfire dashboard
        ],
    )


# Run it immediately when this utils file is imported
# Change use_long_path=False if you want the short filenames again!
setup_logger(use_long_path=False)
