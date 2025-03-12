from plantweb.render import render
import re
import os
import json

if __name__ == '__main__':
    # 读取json文件
    with open("config.json", "r") as f:
        config = json.load(f)
    # 读取输入文件
    input_file = config["input_file"]
    # 读取文件名
    file_name = os.path.basename(input_file).split(".")[0]
    diagrams_name = {"Logic_View":["Class Diagram", "Object Diagram", "State Diagram"],
                    "Development_View":["Package Diagram", "Component Diagram"],
                    "Process_View":["Activity Diagram", "Sequence Diagram", "Collaboration Diagram"],
                    "Physical_View":["Deployment Diagram", "Container Diagram"],
                    "Scenario_View":["Use Case Diagram"]}
    with open("C:\\Research\\MAAD\\demo\\demo_v2\\output\\" + file_name +"\\Designer\\UML.txt") as f:
        content = f.read()
    uml_matches = re.findall(r"@startuml(.*?)@enduml",  content, re.DOTALL)
    expected_diagram_count = sum(len(v) for v in diagrams_name.values())
    if len(uml_matches) != expected_diagram_count:
        print(f"Warning: Expected {expected_diagram_count} diagrams, but found {len(uml_matches)}.")
    index = 0
    for view, diagrams in diagrams_name.items():
        for diagram in diagrams:
            uml_content = f"@startuml{uml_matches[index]}@enduml"
            output = render(
            uml_content,
            engine='plantuml',
            format='svg',
            cacheopts={
                'use_cache': False
            })
            rootname = os.path.join(
                r"C:\\Research\\MAAD\\demo\\demo_v2\\output\\",
                file_name.split(".")[0],
                "Designer",
                f"{view}_{diagram.replace(' ', '_')}.svg"
            )
            print(rootname)
            # 确保目录存在
            os.makedirs(os.path.dirname(rootname), exist_ok=True)
            # 保存文件
            with open(rootname, "wb") as f:
                f.write(output[0])
            index = index + 1