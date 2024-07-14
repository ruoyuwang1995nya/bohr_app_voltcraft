#from dp.launching.typing import BaseModel
from dp.launching.report import Report, ReportSection, ChartReportElement, AutoReportElement
from typing import (
        List,
        Dict,
        Union
)
from pathlib import Path
import json
prop_types=[
    "msd"
]

naive_report = Report(title='Docking Example Result', 
        sections=[],
        name='test',
        description='The provided protein and ligand pair works perfect')



def get_msd_conf(
        task_list: List[Union[str,Path]]
):
    elements=[]
    for task_path in task_list:
        print(task_path)
        if isinstance(task_path,str):
            task_path=Path(task_path)
        with open(task_path/"result_task.json",'r') as fp:
            res=json.load(fp)
        elements.append(
            AutoReportElement(
                path= task_path/"msd.png",
                description="Diffusion coefficient: %s\nIon conductivity: %s"%(
                        res.get("diffusion_coef",0.),
                        res.get("sigma",0.))        
                )
        )
    return ReportSection(
            ncols=len(task_list),
            elements=elements
    )
    
def get_conf_properties(
    conf_path: Union[str,Path]
):
    sections=[]
    if isinstance(conf_path,str):
        conf_path=Path(conf_path)
    prop_dict={}
    for prop in prop_types:
        prop_dict[prop] = [dir for dir in conf_path.iterdir() if dir.is_dir() and prop in dir.name][0]
    if prop_path:=prop_dict.get("msd"):
        sections.append(get_msd_conf(
             [task for task in prop_path.iterdir() if task.is_dir() and "task" in task.name]
        ))
    print(sections)
    return Report(
            title="Results",
            sections=sections,
            name=conf_path.name
    )
         
#def gen_report()

if __name__ == '__main__':
    returns_dir=Path('./outputs/workdir/returns')
    [get_conf_properties(conf).save(str('./')) for\
        conf in returns_dir.iterdir() if conf.is_dir()\
        and conf.name.startswith("conf.")]