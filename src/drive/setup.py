from setuptools import setup
import os
from glob import glob

package_name = 'drive'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share',package_name,'launch'),glob('launch/*')),
        (os.path.join('share',package_name,'world'),glob('world/*')),
        (os.path.join('lib',package_name),glob('scripts/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='scientist',
    maintainer_email='scientist@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "video_recording_node = drive.video_recorder:main",
            "driver = drive.driving_node:main",
            "sdf_spawner = drive.sdf_spawner:main",
        ],
    },
)
