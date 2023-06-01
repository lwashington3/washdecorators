from setuptools import setup

with open("README.md", 'r') as f:
	long_description = f.read()


project_name = "washdecorators"
git_url = f"https://github.com/lwashington3/{project_name}"


setup(
	name=project_name,
	version="1.1.0",
	author="Len Washington III",
	author_email="l.washingtoniii.27@gmail.com",
	description="Common function decorators module",
	include_package_data=True,
	long_description=long_description,
	long_description_content_type="test/markdown",
	url=git_url,
	project_urls={
		"Bug Tracker": f"{git_url}/issues"
	},
	license="MIT",
	packages=[project_name],
	install_requires=["requests"]
)
