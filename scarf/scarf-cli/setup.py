from setuptools import setup

setup(
    name='scarfcli',
    version='0.1.0',
    py_modules=['scarfcli'],
    install_requires=[
        'Click',
        'scarf',
    ],
    entry_points={
        'console_scripts': [
            'scarfcli = scarfcli:cli',
        ],
    },
)
