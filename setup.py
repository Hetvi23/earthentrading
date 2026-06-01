# Shim for older `bench get-app` versions that read setup.py instead of
# pyproject.toml. The canonical metadata lives in pyproject.toml; this file
# exists so bench's `get_app_name()` (regex-matches `name="…"`) succeeds.

from setuptools import find_packages, setup

setup(
	name="earthentrading",
	version="0.0.1",
	description="Trading CRM for Earth",
	author="Earth Trading",
	author_email="admin@earthentrading.local",
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
)
