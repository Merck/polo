from setuptools import setup, find_packages

setup(
    name='POLO',
    version='0.1.0',
    author='Charles A. Lesburg',
    author_email='charles.lesburg@merck.com',
    license='See LICENSE file',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask==1.1.1',
        'Flask-Cors==3.0.9',
        'SQLAlchemy==1.3.10',
        'mysqlclient==1.3.14',
        'pyodbc==4.0.27',
        'requests-oauthlib==1.3.0'
    ]
)
