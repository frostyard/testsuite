"""Pull the shared step vocabulary into this suite.

Importing the module is what registers the steps — behave collects decorators at
import time, so there is nothing to re-export here.
"""

from tests.shared import steps  # noqa: F401
