import argparse
import os
import subprocess
import uuid
import sys

from IPython.core.magic import register_line_cell_magic
from IPython.display import SVG

# Import urlparse() & urlretrieve() for either Python 2 or 3
if sys.version_info >= (3,):
    from urllib.parse import urlparse
    from urllib.request import urlretrieve
else:
    from urlparse import urlparse
    from urllib import urlretrieve

# Dummy import to ensure plantweb module is present
import plantweb

__title__ = "iplantuml"
__description__ = "Package which adds a PlantUML cell magic to IPython."
__uri__ = "https://github.com/jbn/iplantuml"
__doc__ = __description__ + " <" + __uri__ + ">"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2017-8 John Bjorn Nelson"
__version__ = "0.3.0"
__author__ = "John Bjorn Nelson"
__email__ = "jbn@abreka.com"

PLANTUMLPATH = '/usr/local/bin/plantuml.jar'


def plantuml_exec(*file_names, **kwargs):
    """
    Given a list of UML documents, generate corresponding SVG diagrams.

    :param file_names: the filenames of the documents for parsing by PlantUML.
    :param kwargs: optionally `plantuml_path`, indicating where the PlantUML
        jar file resides.
    :return: the path to the generated SVG UML diagram.
    """
    plantuml_path = kwargs.get('plantuml_path', PLANTUMLPATH)

    cmd = ["java",
           "-splash:no",
           "-jar", plantuml_path,
           "-tsvg"] + list(file_names)

    subprocess.check_call(cmd, shell=False, stderr=subprocess.STDOUT)

    return [os.path.splitext(os.path.basename(f))[0] + ".svg" for f in file_names]

def plantuml_web(*file_names, **kwargs):
    """
    Given a list of UML documents, generate corresponding SVG diagrams, using
    PlantUML's web service via the plantweb module.

    :param file_names: the filenames of the documents for parsing by PlantUML.
    :return: the path to the generated SVG UML diagram.
    """

    cmd = ["plantweb",
           "--format",
           "auto"] + list(file_names)

    subprocess.check_call(cmd, shell=False, stderr=subprocess.STDOUT)

    return [os.path.splitext(os.path.basename(f))[0] + ".svg" for f in file_names]

@register_line_cell_magic
def plantuml(line, cell=None):
    """
    Generate and inline the SVG portrayal of the given PlantUML UML spec.

    :param line: if not empty, it is the base file name to give to the
        serialized cell contents and the generated SVG files.
    :param cell: the PlantUML language UML specification.
    :return: a IPython SVG object for the diagram or None given error.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, help="render using specified path or url")
    parser.add_argument("-j", "--jar", type=str, help="render using plantuml.jar (default is web service)")
    parser.add_argument("-n", "--name",  type=str, help="persist diagram as <name>.uml and <name>.svg after rendering")
    parser.add_argument("-p", "--plantuml-path", type=str, help="specify PlantUML jar path (default=%s)" % PLANTUMLPATH)
    args = parser.parse_args(line.split() if line else "")

    retain_uml = retain_svg = args.name is not None
    base_name = args.name or str(uuid.uuid4())
    use_web = not (args.jar or args.plantuml_path)

    if not args.file:
        uml_path = base_name + ".uml"
        with open(uml_path, 'w') as fp:
            fp.write(cell)
    else:
        location = args.file
        url = urlparse(location)
        if url.scheme in ['', 'file']:
            uml_path = url.path
            retain_uml = True
        else:
            uml_path = base_name + ".uml"
            urlretrieve(location, uml_path)

    try:
        output = plantuml_web(uml_path) if use_web else plantuml_exec(uml_path, plantuml_path=os.path.abspath(args.plantuml_path or PLANTUMLPATH))
        svg_path = output[0]
        return SVG(filename=svg_path)
    finally:
        if not retain_uml and os.path.exists(uml_path): os.unlink(uml_path)
        if not retain_svg and os.path.exists(svg_path): os.unlink(svg_path)

