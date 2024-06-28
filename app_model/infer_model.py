from dp.launching.typing import BaseModel, Field
from dp.launching.typing import InputFilePath, OutputDirectory
from dp.launching.typing import Int, Float, List, Enum, String, Dict, Boolean, Optional
from dp.launching.typing.addon.sysmbol import Equal
import dp.launching.typing.addon.ui as ui
from dp.launching.typing import (
    BohriumUsername, 
    BohriumTicket, 
    BohriumProjectId, 
    BohriumJobType,
    BohriumMachineType,
    BohriumPlatform
)
from dp.launching.typing import (
    DflowArgoAPIServer, DflowK8sAPIServer,
    DflowAccessToken, DflowStorageEndpoint,
    DflowStorageRepository, DflowLabels
)
from dp.launching.cli import (
    SubParser,
    default_minimal_exception_handler,
    run_sp_and_exit,
)

inter_group = ui.Group('Interaction Type', 'Define interatomic description')
inference_group =ui.Group('Inference Details', 'Inference Details')


class InjectConfig(BaseModel):
    # Bohrium config
    bohrium_username: BohriumUsername
    bohrium_ticket: BohriumTicket
    bohrium_project_id: BohriumProjectId
    bohrium_job_type: BohriumJobType = Field(default=BohriumJobType.CONTAINER)
    bohrium_machine_type: BohriumMachineType = Field(default=BohriumMachineType.C8_M31_1__NVIDIA_T4)
    bohrium_platform: BohriumPlatform = Field(default=BohriumPlatform.ALI)

    # dflow config
    dflow_labels: DflowLabels
    dflow_argo_api_server: DflowArgoAPIServer
    dflow_k8s_api_server: DflowK8sAPIServer
    dflow_access_token: DflowAccessToken
    dflow_storage_endpoint: DflowStorageEndpoint
    dflow_storage_repository: DflowStorageRepository


class UploadFiles(BaseModel):
    datasets: List[InputFilePath] = \
        Field(..., description='Test data for inference.')
    potential_models: Optional[List[InputFilePath]] #= \
        #Field(..., description='Interatomic potential files required during test', )
    parameter_files: Optional[List[InputFilePath]] = \
        Field(None, ftypes=['json'], max_file_count=2,
                description='(Optional) Specify parameter `JSON` files for SSB-indference to override the default settings,\
               (Do not upload if want to do setting manually in the later UI page)',
        )


class GlobalConfig(BaseModel):
    infer_image_name: String = Field(
        default="registry.dp.tech/dptech/deepmd-kit:2024Q1-d23cf3e", 
        description='Image address including dependencies for SSB-indference to run'
    )
    scass_type: String = Field(
        default="c8_m31_1 * NVIDIA T4", 
        description='Bohrium machine node type for MD simulation'
    )
    group_size: Int = Field(
        default=1,
        ge=1,
        description='Number of tasks per parallel run group'
    )
    pool_size: Int = Field(
        default=1,
        ge=1,
        description='For multi tasks per parallel group, the pool size of multiprocessing pool to handle each task (1 for serial, -1 for infinity)'
    )


class InterTypeOptions(String, Enum):
    deepmd = "deepmd"
    
class ModelVersion(String,Enum):
    dpa1='dpa1'
    dpa2='dpa2'
    
@inter_group
class InterOptions(BaseModel):
    inter_type: InterTypeOptions = Field(
        default=InterTypeOptions.deepmd, 
        description='Interatomic pair style type'
    )
    model_version: ModelVersion = Field(
        default=ModelVersion.dpa1,
        description="Choose version of DPA-SSE model"
    )
    type_map: Dict[String, Int] = Field(
        default={
            "Li":0,
            "B":1,
            "O":2,
            "Al":3,
            "Si":4,
            "P":5,
            "S":6,
            "Cl":7,
            "Ga":8,
            "Ge":9,
            "As":10,
            "Br":11,
            "Sn":12,
            "Sb":13,
            "I":14
            },
        description="Element type map (Key for element name (H, He ...); value for mapping order: 0, 1, 2 ...)"
    )


@inter_group
@ui.Visible(InterOptions, "inter_type", Equal, "deepmd")
class DPVersion(BaseModel):
    dpmd_version: String = Field(
        default="3.0.0",
        description="Version DeepMD-Kit"
    )
@inference_group
class InferenceOptions(BaseModel):
    type_map_infer: List[String] =Field(
        default=[
            "Li",
            "B",
            "O",
            "Al",
            "Si",
            "P",
            "S",
            "Cl",
            "Ga",
            "Ge",
            "As",
            "Br",
            "Sn",
            "Sb",
            "I"
        ],
        description="Element type map (Key for element name (H, He ...); value for mapping order: 0, 1, 2 ...)"
    )
        
 
    

class InferenceModel(
    InjectConfig, 
    UploadFiles, 
    GlobalConfig,
    InterOptions, 
    DPVersion,
    InferenceOptions,
    BaseModel
):
    output_directory: OutputDirectory = Field(default='./outputs')

def infer_runner(opts: InferenceModel):
    pass

if __name__ == "__main__":
    run_sp_and_exit(
        {
            "Inference": SubParser(InferenceModel, infer_runner, "Submit MD workflow using LAMMPS"),
        },
        description="Workflow submission for Solid electrolyte models",
        version="0.1.0",
        exception_handler=default_minimal_exception_handler,
    )
