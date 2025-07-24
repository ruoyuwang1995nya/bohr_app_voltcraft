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
relax_group = ui.Group('结构弛豫', 'Define Relaxation Parameters')
eos_group = ui.Group('状态方程 (EOS)', 'Equation of State (EOS)')
elastic_group = ui.Group('弹性常数与弹性模量', 'Elastic const & moduli')
msd_group = ui.Group('均方位移 (MSD)','Mean square displacement (MSD)')


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
    configurations: List[InputFilePath] = \
        Field(...,
              title='结构文件', 
              description='POSCAR格式,可提供多个')
    potential_models: Optional[List[InputFilePath]] = \
        Field(None, 
            title='自定义的原子力场文件',
            description='如使用预训练DPA-SSE模型则无需上传'
            )
    parameter_files: List[InputFilePath] = \
        Field(None, ftypes=['json'], max_file_count=2,
            title='自定义MD模拟参数文件',
            description='（可选）JSON格式，覆盖默认设置（如使用参数模板则无需上传）',
        )


class GlobalConfig(BaseModel):
    lammps_image_name: String = Field(
        default="registry.dp.tech/dptech/dpmd:2.2.8-cuda12.0", 
        title='LAMMPS镜像',
        description='用于分子动力学模拟的LAMMPS镜像地址'
    )
    lammps_run_command: String = Field(
        default="lmp -in in.lammps", 
        title='LAMMPS运行命令',
        description='命令行命令（LAMMPS的输入文件名应为`in.lammps`）'
    )
    apex_image_name: String = Field(
        default="registry.dp.tech/dptech/prod-11045/apex-dependency:1.2.0", 
        title='APEX镜像',
        description='包含APEX运行依赖的镜像地址 （无需改动）'
    )
    scass_type: String = Field(
        default="c8_m32_1 * NVIDIA V100",
        title='硬件配置', 
        description='用于分子动力学模拟的Bohrium节点硬件型号'
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
    custom='custom'
    
@inter_group
class InterOptions(BaseModel):
    inter_type: InterTypeOptions = Field(
        default=InterTypeOptions.deepmd, 
        title='原子力场类型',
        description='原子力场类型'
    )
    model_version: ModelVersion = Field(
        default=ModelVersion.dpa1,
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
        default="2.2.8",
        title="DeepMD-Kit版本",
        description="DeepMD-Kit版本"
    )
    


@relax_group
class RelaxationParameters(BaseModel):
    custom_relax_lmp_input: Boolean = Field(
        default=False,
        title='高级设置',
        description='用于结构弛豫的LAMMPS输入文件'
    )
    etol: Float = Field(
        default=1e-4,
        ge=0,
        title='能量收敛标准',
        description='eV'
    )
    ftol: Float = Field(
        default=1e-4,
        ge=0,
        title='受力收敛标准',
        description='eV/Angstrom'
    )
    maxiter: Int = Field(
        default=100,
        ge=0,
        title='最大步数',
        description='结构弛豫的最大步数'
    )
    maxeval: Int = Field(
        default=100,
        ge=0,
        title='最大评估次数',
        description='结构弛豫的最大评估次数'
    )



@relax_group
@ui.Visible(RelaxationParameters, "custom_relax_lmp_input", Equal, True)
class RelaxInLmp(BaseModel):
    relax_in_lmp: String = Field(
        default=None,
        format="multi-line",
        title='自定义命令',
        description='LAMMPS input instruction for relaxation'
    )


class CalTypeOptions(String, Enum):
    relaxation = 'relaxation'
    static = 'static'


@eos_group
class EOSOptions(BaseModel):
    select_eos: Boolean = Field(default=False, 
                                title='计算',
                                description='是否进行状态方程（EOS）计算')


@eos_group
@ui.Visible(EOSOptions, "select_eos", Equal, True)
class EOSParameters(BaseModel):
    custom_eos_calc: Boolean = Field(
        default=False,
        title='高级设置',
        description='自定义EOS计算的高级设置'
    )
    eos_cal_type: CalTypeOptions = Field(
        default=CalTypeOptions.relaxation,
        render_type="radio",
        title='计算类型',
        description='MD计算类型'
    )
    vol_start: Float = Field(
        default=0.8,
        gt=0,
        title='起始体积缩放系数',
        description='初始体积*系数'
    )
    vol_end: Float = Field(
        default=1.2,
        gt=0,
        title='终止体积缩放系数',
        description='初始体积*系数'
    )
    vol_step: Float = Field(
        default=0.05,
        gt=0,
        title='体积缩放间隔',
        description='体积缩放间隔'
    )
    vol_abs: Boolean = Field(
        default=False,
        title='使用绝对体积',
        description='是否采用绝对体积'
    )


@eos_group
@ui.Visible(EOSParameters, "custom_eos_calc", Equal, True)
class EOSAdvance(BaseModel):
    eos_etol: Float = Field(
        default=0,
        ge=0,
        title='能量收敛标准',
        description='结构弛豫的能量收敛标准'
    )
    eos_ftol: Float = Field(
        default=1e-10,
        ge=0,
        title='受力收敛标准',
        description='结构弛豫的受力收敛标准'
    )
    eos_maxiter: Int = Field(
        default=5000,
        ge=0,
        title='最大步数',
        description='结构弛豫的最大步数'
    )
    eos_maxeval: Int = Field(
        default=500000,
        ge=0,
        title='最大评估次数',
        description='结构弛豫的最大评估次数'
    )
    eos_relax_pos: Boolean = Field(
        default=True,
        title='弛豫原子位置',
        description='弛豫中允许改变原子位置'
    )
    eos_relax_shape: Boolean = Field(
        default=True,
        title='弛豫晶胞形状',
        description='弛豫中允许改变晶胞形状'
    )
    eos_relax_vol: Boolean = Field(
        default=False,
        title='弛豫晶胞体积',
        description='弛豫中允许改变晶胞体积'
    )
    eos_in_lmp: String = Field(
        default=None,
        format="multi-line",
        title='自定义命令',
        description='用于EOS计算的LAMMPS输入参数，覆盖模板输入参数'
    )


@elastic_group
class ElasticOptions(BaseModel):
    select_elastic: Boolean = Field(default=False,
                                title='计算',
                                    description='是否进行弹性性质计算')

@elastic_group
@ui.Visible(ElasticOptions, "select_elastic", Equal, True)
class ElasticParameters(BaseModel):
    custom_elastic_calc: Boolean = Field(
        default=False,
        title='高级设置',
        description='自定义弹性性质计算的高级LAMMPS设置'
    )
    elastic_cal_type: CalTypeOptions = Field(
        default=CalTypeOptions.relaxation,
        render_type="radio",
        title='计算类型',
        description='分子动力学计算类型'
    )
    norm_deform: Float = Field(
        default=0.01,
        gt=0,
        title='法向应变',
        description='法向应变大小'
    )
    shear_deform: Float = Field(
        default=0.01,
        gt=0,
        title='剪切应变',
        description='剪切应变大小'
    )


@elastic_group
@ui.Visible(ElasticParameters, "custom_elastic_calc", Equal, True)
class ElasticAdvance(BaseModel):
    elastic_etol: Float = Field(
        default=0,
        ge=0,
        title='能量收敛标准',
        description='结构弛豫的能量收敛标准'
    )
    elastic_ftol: Float = Field(
        default=1e-10,
        ge=0,
        title='受力收敛标准',
        description='结构弛豫的受力收敛标准'
    )
    elastic_maxiter: Int = Field(
        default=5000,
        ge=0,
        title='最大步数',
        description='结构弛豫的最大步数'
    )
    elastic_maxeval: Int = Field(
        default=500000,
        ge=0,
        title='最大评估次数',
        description='结构弛豫的最大评估次数'
    )
    elastic_relax_pos: Boolean = Field(
        default=True,
        title='弛豫原子位置',
        description='弛豫中允许改变原子位置'
    )
    elastic_relax_shape: Boolean = Field(
        default=False,
        title='弛豫晶胞形状',
        description='弛豫中允许改变晶胞形状'
    )
    elastic_relax_vol: Boolean = Field(
        default=False,
        title='弛豫晶胞体积',
        description='弛豫中允许改变晶胞体积'
    )
    elastic_in_lmp: String = Field(
        default=None,
        format="multi-line",
        title='自定义命令',
        description='用于弹性性质计算的自定义LAMMPS输入参数，覆盖模板输入参数'
    )

@msd_group
class MSDOptions(BaseModel):
    select_msd: Boolean = Field(default=False, 
                                title='计算',    
                                description='是否进行均方位移（MSD）计算')
@msd_group
@ui.Visible(MSDOptions, "select_msd", Equal, True)
class MSDParameters(BaseModel):
    msd_supercell: List[Int] = Field(
        default=[1,1,1],
        title='扩胞系数',
        description='超胞的扩胞系数'
    )
    
    msd_ion_list: List[String] = Field(
        default=['Li'],
        title='离子种类',
        description='需要计算MSD的离子种类，可多选'
    )
    msd_temperature: List[Float] = Field(
        default=[300.0],
        title='模拟温度 (K)',
        description='模拟温度'
    )
    msd_equi_step: Int = Field(
        default=1000,
        ge=0,
        title='预平衡步数',
        description='使模拟体系达到对应温度的平衡状态'
    )
    msd_run_step: Int = Field(
        default=10000,
        ge=0,
        title='NVT模拟步数',
        description='用于MSD计算'
    )
    msd_out_step: Int = Field(
        default=100,
        ge=0,
        title='MSD的输出间隔',
        description='单位：模拟步数'
    )
    msd_dt: Float = Field(
        default=1.,
        ge=1,
        title='原子步步长',
        description='单位：fs'
    )
    msd_in_lmp: String = Field(
        default=None,
        format="multi-line",
        title='自定义命令',
        description='用于MSD计算的自定义LAMMPS输入参数，覆盖模板输入参数'
    )
    skip_sigma: Boolean = Field(
        default=False,
        title='是否跳过离子电导率计算',
        description="是否采用Nernst-Einstein关系计算离子电导率"
    )

    


class LammpsModel(
    InjectConfig, 
    UploadFiles, 
    GlobalConfig,
    InterOptions, 
    CustomPotential,
    DPVersion,
    RelaxationParameters,
    RelaxInLmp,
    EOSOptions,
    EOSParameters,
    EOSAdvance,
    ElasticOptions,
    ElasticParameters,
    ElasticAdvance,
    MSDOptions,
    MSDParameters,
    BaseModel
):
    output_directory: OutputDirectory = Field(default='./outputs')

def lmp_runner(opts: LammpsModel):
    pass

if __name__ == "__main__":
    run_sp_and_exit(
        {
            "LAMMPS": SubParser(LammpsModel, lmp_runner, "Submit MD workflow using LAMMPS"),
        },
        description="Workflow submission for Solid electrolyte models",
        version="0.1.0",
        exception_handler=default_minimal_exception_handler,
    )
