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

inter_group = ui.Group('原子力场类型', 'Define interatomic description')


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
        Field(..., 
              title='结构数据集',
              description='待预测的结构数据集.')
    potential_models: Optional[List[InputFilePath]] = \
        Field(None, 
              itle='自定义的原子力场文件',
              description='如使用预训练DPA-SSE模型则无需上传', )
    parameter_files: Optional[List[InputFilePath]] = \
        Field(None, ftypes=['json'], max_file_count=2,
               title='自定义参数文件',
              description='（可选）JSON格式，覆盖默认设置（如使用参数模板则无需上传）'
        )


class GlobalConfig(BaseModel):
    infer_image_name: String = Field(
        default="registry.dp.tech/dptech/deepmd-kit:2024Q1-d23cf3e", 
        title='镜像地址',
        description='包含DPA-SSE模型所需依赖的镜像地址'
    )
    scass_type: String = Field(
        default="c8_m31_1 * NVIDIA T4", 
        title='硬件配置', 
        description='预测任务节点类型'
    )
    group_size: Int = Field(
        default=1,
        ge=1,
        title="任务组大小",
        description='每个任务组（对应一个计算节点）的任务数'
    )
    pool_size: Int = Field(
        default=1,
        ge=1,
        title="并行任务数",
        description='每个任务组中，同时并行计算的任务数量（1为串行，-1为无限）'
    )


class InterTypeOptions(String, Enum):
    deepmd = "deepmd"
    
class ModelVersion(String,Enum):
    dpa1='dpa1'
    dpa2='dpa2'
    custom='custom'
    
@inter_group
class InterOptions(BaseModel):
    inter_type: InterTypeOptions = Field(
        default=InterTypeOptions.deepmd, 
        title='原子力场类型',
        description='原子力场类型'
    )
    model_version: ModelVersion = Field(
        default=ModelVersion.dpa2,
        title='DPA-SSE模型的版本',
        description="选择DPA-SSE模型的版本"
    )

@inter_group
@ui.Visible(InterOptions,"model_version", Equal, ModelVersion.custom)
class CustomPotential(BaseModel):
    type_map: Dict[String, Int] = Field(
        default={},
        title='元素种类映射',
        description="元素符号与力场模型中元素序号的对应关系，使用DPA-SSE则无需提供"
    )


@inter_group
@ui.Visible(InterOptions, "inter_type", Equal, "deepmd")
class DPVersion(BaseModel):
    dpmd_version: String = Field(
        default="3.0.0",
        title="DeepMD-Kit版本",
        description="DeepMD-Kit版本"
    )


class InferenceModel(
    InjectConfig, 
    UploadFiles, 
    GlobalConfig,
    InterOptions, 
    CustomPotential,
    DPVersion,
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
