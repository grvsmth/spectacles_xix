import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spectacles_xix",
    version="0.1.4",
    author="Angus B. Grieve-Smith",
    author_email="angus@grieve-smith.com",
    description="Twitter bot to tweet record of theatrical plays from a database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/grvsmth/spectacles_xix",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)