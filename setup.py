import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="voltcraft_app",
    version="0.0.1",
    author="Ruoyu Wang",
    author_email="ruoyuwang1995@gmail.com",
    description="AI-driven battery simulations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ruoyuwang1995ucas/LAM-SSB.git",
    install_requires=[
        "pydflow>=1.7.83",
        "pymatgen>=2023.8.10",
        'pymatgen-analysis-defects>=2023.8.22',
        "dpdata>=0.2.13",
        "dpdispatcher",
        "matplotlib",
        "seekpath",
        "fpop>=0.0.7",
        "boto3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    package_data={
        'dpa1_model':['models/dpa1/L0-r8/frozen_model.pb'],
        'dpa2_model':['models/dpa2/frozen_model.pth']
        },
    packages=setuptools.find_packages(),
    package_dir={"": "."},
    include_package_data=True
    
)
