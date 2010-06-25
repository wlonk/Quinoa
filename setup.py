
from setuptools import setup, find_packages

setup(
    name='quinoa',
    version='0.3.1',
    author='Kit La Touche',
    author_email='kit.la.t@gmail.com',
    description="This is a base class for making Jabber bots that are aware" \
                " of MUC/groupchat.",
    long_description="""\
This is a simple package for making MUC/groupchat-aware Jabber bots.  It provides a class, quinoa.Bot, which you can subclass to make your own bots.  See the readme for more information.""",
    license="GPL",
    keywords=["jabber", "xmpp", "groupchat", "muc", "bot"],
    url="http://hg.transneptune.net/quinoa",
    install_requires=['xmpppy >= 0.4'],
    package_dir={
        '': 'src'
        },
    packages=find_packages('src'),
    platforms='All',
    classifiers=[
          'Topic :: Communications :: Chat',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Natural Language :: English',
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
        ]
)
