from pathlib import Path
import re
from setuptools import setup, find_packages
import os

def get_version():
    """Reads the version from your_package/__init__.py"""
    init_py = Path(__file__).parent.joinpath("semantic_iot", "__init__.py")
    with open(init_py, "r") as f:
        content = f.read()
    # Using a regular expression to find the version string
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]*)['\"]", content, re.M)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")

# Utility function to read the README file.
def read_long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    readme_path = os.path.join(here, 'test', 'readme.md')
    try:
        with open(readme_path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Long description not available."


# Utility function to read the requirements.txt file.
def read_requirements():
    here = os.path.abspath(os.path.dirname(__file__))
    requirements_path = os.path.join(here, 'requirements.txt')
    try:
        with open(requirements_path, encoding='utf-8') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []


setup(
    name='semantic_iot',
    version=get_version(),
    author='Junsong Du',
    author_email='junsong.du@eonerc.rwth-aachen.de',
    description='A semantic framework to enhence interoperability cross different '
                'IoT platforms',
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/N5GEH/semantic-iot',
    packages=find_packages(
        exclude=["tests", "test", "docker", "Dockerfile", "examples"]
    ),
    include_package_data=True,  # Include non-Python files specified in MANIFEST.in
    package_data={
        # Include any data files in the 'semantic_iot' package
        'semantic_iot': ['*.ttl.jinja2'],
    },
    install_requires=read_requirements(),
    classifiers=[
        'Programming Language :: Python :: 3',  # Specify the Python versions you support
        'License :: OSI Approved :: MIT License',  # Choose an appropriate license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
    # entry_points={
    #     'console_scripts': [
    #         # Add command-line scripts here
    #         # Example:
    #         # 'iot2kg-cli = test.RML_Generator:main',
    #     ],
    # },
)
