import os

from setuptools import find_packages, setup

readme = os.path.join(os.path.dirname(__file__), 'README.md')

with open(readme) as fh:
    long_description = fh.read()

setup(
    name="netbox-paas",
    version="0.3.4",
    description="Enhances NetBox on CloudMyDC's PaaS with advanced management and control features.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Onemind-Services-LLC/netbox-paas/",
    download_url="https://github.com/Onemind-Services-LLC/netbox-paas/",
    author="Abhimanyu Saharan",
    author_email="asaharan@onemindservices.com",
    maintainer="Abhimanyu Saharan",
    maintainer_email="asaharan@onemindservices.com",
    install_requires=["py-jelastic", "croniter<3.0.0", "semver<4.0.0", "requirements-parser"],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platform=[],
    keywords=["netbox", "netbox-plugin"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Django",
        "Programming Language :: Python :: 3",
    ],
)
