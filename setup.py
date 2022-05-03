"""
Setup Module for the swandaskcluster package.
"""
import os

from jupyter_packaging import get_version
import setuptools

name="swandaskcluster"

# Get our version
version = get_version(os.path.join(name, "_version.py"))

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_args = dict(
    name=name,
    version=version,
    url="https://github.com/swan-cern/swan-daskcluster",
    author="SWAN Admins",
    description="Package to create wrappers of Dask clusters to be used from SWAN",
    long_description= long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[
        'dask_lxplus',
        'swanportallocator',
    ],
    zip_safe=False,
    include_package_data=True,
    package_data={
        # Include yaml with default args for SwanHTCondorCluster
        "swandaskcluster": ["*.yaml"],
    },
    python_requires=">=3.6",
    license="AGPL-3.0",
    platforms="Linux, Mac OS X, Windows",
    keywords=["Jupyter", "Notebooks", "SWAN", "CERN"],
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Framework :: Jupyter",
    ],
)


if __name__ == "__main__":
    setuptools.setup(**setup_args)
