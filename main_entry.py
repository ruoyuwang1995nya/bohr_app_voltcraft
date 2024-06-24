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
    return {
        "LAMMPS": SubParser(LammpsModel, lmp_runner, "Running with LAMMPS"),
        #"scan": SubParser(SCANModel, scan_runner, "Run SCAN Model"),
    }

#def to_parser():
#    return  to_runner(
#        LammpsModel,
#        lmp_runner,
##        version="0.0.1",
 #       exception_handler=print_full_traceback#error_handler
 #   )


if __name__ == "__main__":
    import sys
    #to_parser()(sys.argv[2:])
    run_sp_and_exit(
        {
            "LAMMPS": SubParser(LammpsModel, lmp_runner, "Submit MD workflow using LAMMPS"),
        },
        description="Workflow submission for Solid electrolyte models",
        version="0.1.0",
        exception_handler=print_full_traceback,
    )