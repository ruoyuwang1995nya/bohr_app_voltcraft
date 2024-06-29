from pathlib import Path
import zipfile
import os
import shutil
import json
from monty.serialization import loadfn
#from apex.submit import submit_workflow
from ssb.submit import submit_workflow
from .infer_model import InferenceModel
from . import models

default_type_map={
            "Li":0,
            "B":1,
            "O":2,
            "Al":3,
            "Si":4,
            "P": 5,
            "S":6,
            "Cl":7,
            "Sc":8,
            "Ga":9,
            "Ge":10,
            "As":11,
            "Se":12,
            "Br":13,
            "Y":14,
            "Zr":15,
            "In":16,
            "Sn":17,
            "Sb":18,
            "I":19,
            "Dy":20,
            "Ho":21,
            "Er":22,
            "Tm":23,
            "Yb":24,
            "Lu":25,
            "Ta":26
            }

def get_global_config(opts: InferenceModel):
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
        "inference_image_name": opts.infer_image_name,
        "group_size": opts.group_size,
        "pool_size": opts.pool_size,
        "is_bohrium_dflow": True,
    }
    json.dump(global_config, open('global_config_tmp.json', 'w'), indent=2)
    global_config = loadfn('global_config_tmp.json')
    #os.remove('global_config_tmp.json')
    return global_config


def get_interaction(opts: InferenceModel):


    interaction = {
        "type": opts.inter_type,
        #"type_map": opts.type_map,
        "deepmd_version": opts.dpmd_version,
    }
    if opts.model_version == "custom":
        interaction["model"]=[Path(ii).name for ii in opts.potential_models] if len(opts.potential_models) > 1 \
            else Path(opts.potential_models[0])
        interaction["type_map"]=opts.type_map
    elif opts.model_version == "dpa1":
        interaction["model"]="frozen_model.pb"
        interaction["type_map"]=default_type_map
        
    elif opts.model_version == "dpa2":
        interaction["model"]="frozen_model.pth"
        interaction["type_map"]=default_type_map
        
    return interaction



def get_inference(opts: InferenceModel):
    inference_dict = {
        "type_map":[k for k in default_type_map.keys()]
    }
    return inference_dict


def get_parameter_dict(opts: InferenceModel):
    inter_param=get_interaction(opts)
    parameter_dict = {
        "structures":  ["returns/sys.*/*"],
        "interaction": inter_param,
        "direct_inference":[k for k in inter_param["type_map"].keys()]
    }
    return parameter_dict


def infer_runner(opts: InferenceModel):
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
    for ii in opts.datasets:
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