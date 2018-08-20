from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="flaskbb-ranks",
        version="0.0.1",
        author="Alec Nikolas Reiter",
        license="MIT",
        description="Adds user ranks to FlaskBB",
        include_package_data=True,
        packages=find_packages("src"),
        package_dir={"": "src"},
        install_requires=["FlaskBB>=2.0,<3.0", "attrs>=18.1.0,<19"],
        entry_points={"flaskbb_plugins": "ranks = flaskbb_ranks"},
    )
