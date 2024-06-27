from pathlib import Path
import zipfile
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
        "inference_image_name": opts.lammps_image_name,
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
        
    elif opts.model_version == "dpa2":
        interaction["model"]="frozen_model.pth"
        #interaction["potcar_prefix"]="models/dpa1/L0-r8"
        
    return interaction



def get_inference(opts: LammpsModel):
    inference_dict = {
        "type_map":opts.type_map_infer
    }
    return inference_dict


def get_parameter_dict(opts: LammpsModel):
    parameter_dict = {
        "structures":  ["returns/sys.*"],
        "interaction": get_interaction(opts),
    }
    if get_inference(opts):
        parameter_dict["direct_inference"] = get_inference(opts)
    return parameter_dict


def infer_runner(opts: LammpsModel):
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
        conf_dir = returns_dir / ("sys.%06d" % (count))
        os.chdir(cwd)
        with zipfile.ZipFile(ii, 'r') as zip_ref:
            zip_ref.extractall(conf_dir)
        count += 1

    # papare potential files
    # copy models to workdir
    #__self__
    if opts.model_version == "dpa1":
        model_path=Path(models.__path__[0])/'dpa1/L0-r8/frozen_model.pb'
        shutil.copy(model_path,workdir) 
    
    if opts.model_version == "dpa2":
        model_path=Path(models.__path__[0])/'dpa2/frozen_model.pth'
        shutil.copy(model_path,workdir) 
    
    
    if opts.potential_models:
        for ii in opts.potential_models:
            shutil.copy(ii, workdir)
    
    os.chdir(workdir)
    # papare global config
    #config_dict = get_global_config(opts)
    config_dict = get_global_config(opts)
    
    # papare parameter files
    parsed_parameter_dict = get_parameter_dict(opts)
    json.dump(parsed_parameter_dict, open('parameter_tmp.json', 'w'), indent=2)
    parsed_parameter_dict = loadfn('parameter_tmp.json')
    print(parsed_parameter_dict)
    parameter_dicts.append(parsed_parameter_dict)
    
    # submit APEX workflow
    submit_workflow(
        parameter=parameter_dicts,
        config_dict=config_dict,
        work_dir=['./'],
        flow_type="inference",
        labels=opts.dflow_labels
    )

    os.chdir(cwd)
    shutil.copytree(workdir, Path(opts.output_directory)/'workdir', dirs_exist_ok = True)

if __name__ == "__main__":
    print(models.__path__)