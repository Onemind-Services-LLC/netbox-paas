from setuptools import find_packages, setup

setup(
    name="netbox-cloud-pilot",
    version="0.0.1",
    description="NetBox Clouds",
    long_description="Manage NetBox on VAP infrastructure",
    url="https://github.com/Onemind-Services-LLC/netbox-cloud-pilot/",
    download_url="https://github.com/Onemind-Services-LLC/netbox-cloud-pilot/",
    author="Abhimanyu Saharan",
    author_email="asaharan@onemindservices.com",
    maintainer="Prince Kumar",
    maintainer_email="pkumar@onemindservices.com",
    install_requires=["py-jelastic<0.1.0", "croniter<3.0.0"],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platform=[],
    keywords=["netbox", "netbox-plugin"],
    classifiers=[
        "Development Status :: 1 - Pre-Alpha",
        "Framework :: Django",
        "Programming Language :: Python :: 3",
    ],
)
