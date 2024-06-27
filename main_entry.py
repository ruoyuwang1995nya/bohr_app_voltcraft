from dp.launching.cli import (
    SubParser,
    to_runner,
    run_sp_and_exit,
)

from app_model.lmp_model import LammpsModel
from app_model.lmp_runner import lmp_runner
from app_model.infer_model import InferenceModel
from app_model.infer_runner import infer_runner
import traceback

def print_full_traceback(exc):
    while exc:
        traceback.print_exception(type(exc), exc, exc.traceback)
        exc = exc.cause or exc.context


def to_parser():
    return {
        "LAMMPS": SubParser(LammpsModel, lmp_runner, "Running with LAMMPS"),
        "Inference": SubParser(InferenceModel, infer_runner, "Inference with DPA-SSE")
    }


if __name__ == "__main__":
    import sys
    #to_parser()(sys.argv[2:])
    run_sp_and_exit(
        to_parser(),
        description="Workflow submission for Solid electrolyte models",
        version="0.1.0",
        exception_handler=print_full_traceback,
    )