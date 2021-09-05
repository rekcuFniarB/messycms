import setuptools

setuptools.setup(
    name='messycms',
    version='0.0.2',
    description='MessyCMS: an experimental Django based CMS.',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Content Management System',
        'Framework :: Django',
    ],
    author='Pyroman',
    author_email='pyroman-github@ofthe.top',
    python_requires='>=3.5',
    install_requires=[
        #'examplelib==1.0.1',
        #'examplellib2>=2.2',
        'django',
        'django-mptt',
        'requests',
    ],
    zip_safe=False,
    include_package_data=True,
    package_dir={"": "src"},   # tell distutils packages are under src
    #packages=setuptools.find_packages("src"),  # include all packages under src
    packages=[
        'MessyCMS',
        'MessyCMS.plugins',
        'MessyCMS.plugins.tgimages',
        'MessyCMS.plugins.tgimages.templates.tgimages',
        'MessyCMS.static.messycms.js',
        'MessyCMS.static.messycms.css',
        'MessyCMS.templatetags',
        'MessyCMS.templates',
        'MessyCMS.templates.messycms',
        'MessyCMS.templates.messycms.blocks',
    ],
    package_data={
        '': ['*.conf', '*.md', '*.txt', '*.html', '*.js', '*.css', 'etc/*']
    },
)
