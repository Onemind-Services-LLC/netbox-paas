from setuptools import find_packages, setup

description = "Enhances NetBox on CloudMyDC's VAP with advanced management and control features."

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="netbox-cloud-pilot",
    version="0.0.1",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Onemind-Services-LLC/netbox-cloud-pilot/",
    download_url="https://github.com/Onemind-Services-LLC/netbox-cloud-pilot/",
    author="Abhimanyu Saharan",
    author_email="asaharan@onemindservices.com",
    maintainer="Abhimanyu Saharan",
    maintainer_email="asaharan@onemindservices.com",
    install_requires=["py-jelastic", "croniter<3.0.0", "semver<4.0.0"],
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
