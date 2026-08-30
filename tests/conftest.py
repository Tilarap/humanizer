"""Test environment setup that never relies on a developer's API key."""

import os

os.environ["OPENAI_API_KEY"] = " "
