from pathlib import Path
import os
import shutil
import json
from monty.serialization import loadfn
#from apex.submit import submit_workflow
from ssb.submit import submit_workflow
from .lmp_model import LammpsModel
from . import models



def get_global_config(opts: LammpsModel):
    global_config = {        
        "dflow_config": {
            "host": opts.dflow_argo_api_server,
            "k8s_api_server": opts.dflow_k8s_api_server,
            "token": opts.dflow_access_token,
            "dflow_labels": opts.dflow_labels.get_value()
        },
        "dflow_s3_config": {
            "endpoint": opts.dflow_storage_endpoint,
            "repo_key": opts.dflow_storage_repository
        },
        "bohrium_config":{
            "username": opts.bohrium_username,
            "ticket": opts.bohrium_ticket,
            "projectId": opts.bohrium_project_id
        },
        "machine": {
            "batch_type": "Bohrium",
            "context_type": "Bohrium",
            "remote_profile": {
                "email": opts.bohrium_username,
                "password": opts.bohrium_ticket,
                "program_id": int(opts.bohrium_project_id),
                "input_data": {
                    "job_type": opts.bohrium_job_type,
                    "platform": opts.bohrium_platform,
                    "scass_type": opts.scass_type
                    },
                },
            },
        "apex_image_name": opts.apex_image_name,
        "run_image_name": opts.lammps_image_name,
        "group_size": opts.group_size,
        "pool_size": opts.pool_size,
        "run_command": opts.lammps_run_command,
        "is_bohrium_dflow": True,
    }
    json.dump(global_config, open('global_config_tmp.json', 'w'), indent=2)
    global_config = loadfn('global_config_tmp.json')
    #os.remove('global_config_tmp.json')
    return global_config


def get_interaction(opts: LammpsModel):

    interaction = {
        "type": opts.inter_type,
        "type_map": opts.type_map,
        "deepmd_version": opts.dpmd_version,
    }
    if opts.potential_models:
        interaction["model"]=[Path(ii).name for ii in opts.potential_models] if len(opts.potential_models) > 1 \
            else Path(opts.potential_models[0])
    elif opts.model_version == "dpa1":
        interaction["model"]="frozen_model.pb"
        #interaction["potcar_prefix"]="models/dpa1/L0-r8"
        
        
    if opts.relax_in_lmp:
        with open('custom_relax_in.lammps', 'w') as f:
            f.write(opts.relax_in_lmp)
        interaction["in_lammps"] = "custom_relax_in.lammps"
    return interaction


def get_relaxation(opts: LammpsModel):
    relaxation = {
        "cal_setting": {
            "etol": opts.etol,
            "ftol": opts.ftol,
            "maxiter": opts.maxiter,
            "maxeval": opts.maxeval,
            "relax_pos": opts.relax_pos,
            "relax_shape": opts.relax_shape,
            "relax_vol": opts.relax_vol,
        }
    }
    return relaxation


def get_properties(opts: LammpsModel):
    properties = []
    if opts.select_eos:
        eos_params = {
            "type": "eos",
            "skip": False,
            "vol_start": opts.vol_start,
            "vol_end": opts.vol_end,
            "vol_step": opts.vol_step,
            "vol_abs": opts.vol_abs,
            "cal_type": opts.eos_cal_type
        }
        if opts.custom_eos_calc:
            eos_params["cal_setting"] = {
                "etol": opts.eos_etol,
                "ftol": opts.eos_ftol,
                "maxiter": opts.eos_maxiter,
                "maxeval": opts.eos_maxeval,
                "relax_pos": opts.eos_relax_pos,
                "relax_shape": opts.eos_relax_shape,
                "relax_vol": opts.eos_relax_vol,
            }
            if opts.eos_in_lmp:
                with open('custom_eos_in.lammps', 'w') as f:
                    f.write(opts.eos_in_lmp)
                eos_params["cal_setting"]["input_prop"] = "custom_eos_in.lammps"
        properties.append(eos_params)

    if opts.select_elastic:
        elastic_params = {
            "type": "elastic",
            "skip": False,
            "norm_deform": opts.norm_deform,
            "shear_deform": opts.shear_deform,
            "cal_type": opts.elastic_cal_type
        }
        if opts.custom_elastic_calc:
            elastic_params["cal_setting"] = {
                "etol": opts.elastic_etol,
                "ftol": opts.elastic_ftol,
                "maxiter": opts.elastic_maxiter,
                "maxeval": opts.elastic_maxeval,
                "relax_pos": opts.elastic_relax_pos,
                "relax_shape": opts.elastic_relax_shape,
                "relax_vol": opts.elastic_relax_vol,
            }
            if opts.elastic_in_lmp:
                with open('custom_elastic_in.lammps', 'w') as f:
                    f.write(opts.elastic_in_lmp)
                elastic_params["cal_setting"]["input_prop"] = "custom_elastic_in.lammps"
        properties.append(elastic_params)
        
    if opts.select_msd:
        msd_params={
            "type":"msd",
            "using_template": opts.msd_use_template,
            "temperature": opts.msd_temperature,
            "supercell": opts.msd_supercell,
        }
        if opts.msd_use_template:
            msd_params["cal_setting"] = {
                "equi_setting":{
                        "run-step":opts.msd_equi_step
                    },
                "prop_setting": {
                    "run-step":opts.msd_run_step,
                    "msd_step":opts.msd_out_step
                }
            }
            ion_list={}
            for k in opts.msd_ion_list:
                ion_list[k]=opts.type_map.get(k,0)
            msd_params["res_setting"]={
                "filename":'msd.out',
                "delimiter": " ",
                "ion_list":ion_list,   #opts.msd_ion_list,
                "dt":1,
                "diff_cvt":1e-5,
                "skip_sigma":opts.skip_sigma
        }
            if opts.elastic_in_lmp:
                with open('custom_elastic_in.lammps', 'w') as f:
                    f.write(opts.elastic_in_lmp)
                msd_params["cal_setting"]["input_prop"] = "custom_elastic_in.lammps"
        else:
            msd_params["res_setting"]={
                "filename":opts.msd_res_filename,
                "delimiter": opts.msd_res_del,
                "ion_list":opts.msd_ion_list,
                "dt":opts.msd_res_dt,
                "diff_cvt":opts.msd_res_diff_cvt
        }
        properties.append(msd_params)

    return properties


def get_parameter_dict(opts: LammpsModel):
    parameter_dict = {
        "structures":  ["returns/conf.*"],
        "interaction": get_interaction(opts),
        "relaxation": get_relaxation(opts)
    }
    if get_properties(opts):
        parameter_dict["properties"] = get_properties(opts)
        
    return parameter_dict


def lmp_runner(opts: LammpsModel):
    cwd = Path.cwd()
    parameter_dicts = []
    print('start running....')
    workdir = cwd / 'workdir'
    returns_dir = workdir / 'returns'
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    workdir.mkdir()
    returns_dir.mkdir()

    # papare input POSCAR
    count = 0
    for ii in opts.configurations:
        os.chdir(workdir)
        conf_dir = returns_dir / ("conf.%06d" % count)
        conf_dir.mkdir()
        os.chdir(cwd)
        shutil.copy(ii, conf_dir/'POSCAR')
        count += 1

    # papare potential files
    # copy models to workdir
    #__self__
    if opts.model_version == "dpa1":
        model_path=Path(models.__path__[0])/'dpa1/L0-r8/frozen_model.pb'
    #if os.path.isfile(workdir/'models'):
    #    os.remove(workdir/'models')
    shutil.copy(model_path,workdir) 
    
    if opts.model_version == "dpa2":
        model_path=Path(models.__path__[0])/'dpa2/frozen_model.pt'
    shutil.copy(model_path,workdir) 
    
    
    if opts.potential_models:
        for ii in opts.potential_models:
            shutil.copy(ii, workdir)
    
    os.chdir(workdir)
    # papare global config
    #config_dict = get_global_config(opts)
    config_dict = get_global_config(opts)
    
    # papare parameter files
    if opts.parameter_files:
        for ii in opts.parameter_files:
            os.chdir(cwd)
            with open(ii, 'r') as f:
                j = json.load(f)
                j["structures"] = ["returns/conf.*"]
            with open(ii, 'w') as r:
                json.dump(j, r, indent=2)
            shutil.copy(ii, workdir)
            parameter_dicts.append(loadfn(ii))
            os.chdir(workdir)
    else:
        parsed_parameter_dict = get_parameter_dict(opts)
        json.dump(parsed_parameter_dict, open('parameter_tmp.json', 'w'), indent=2)
        parsed_parameter_dict = loadfn('parameter_tmp.json')
        #interaction=get_interaction(opts)
        print(parsed_parameter_dict)
        parameter_dicts.append(parsed_parameter_dict)
    
    print(parameter_dicts[0])
    with open('param.json','w') as f:
        json.dump(parameter_dicts[0],f,indent=4)
    # submit APEX workflow
    submit_workflow(
        parameter=parameter_dicts,
        config_dict=config_dict,
        work_dir=['./'],
        flow_type=None,
        labels=opts.dflow_labels
    )

    os.chdir(cwd)
    shutil.copytree(workdir, Path(opts.output_directory)/'workdir', dirs_exist_ok = True)

if __name__ == "__main__":
    print(models.__path__)