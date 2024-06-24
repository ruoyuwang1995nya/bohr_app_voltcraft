from dp.launching.cli import (
    SubParser,
    to_runner,
    run_sp_and_exit,
)

from app_model.lmp_model import LammpsModel
from app_model.lmp_runner import lmp_runner
import traceback

def print_full_traceback(exc):
    while exc:
        traceback.print_exception(type(exc), exc, exc.traceback)
        exc = exc.cause or exc.context



def to_parser():
    return  to_runner(
        LammpsModel,
        lmp_runner,
        version="0.0.1",
        exception_handler=print_full_traceback#error_handler
    )

#{
#        "1-LAMMPS": SubParser(LammpsModel, lmp_runner, "Submit MD workflow using LAMMPS"),
#    }

#def error_handler(exc):
#    print(f"Error: {exc}")


def main():
    # excute APEX app main flow
    run_sp_and_exit(
        to_parser(),
        description="Voltcraft workflow submission",
        version="1.2.0",
        #exception_handler=error_handler
    )


if __name__ == "__main__":
    import shutil
    import os
    import sys
    if not os.path.isdir('models'):
        shutil.copytree('/models','models')
    #main()
    to_parser()(sys.argv[2:])