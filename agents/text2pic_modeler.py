from plantweb.render import render
import re
import os

if __name__ == '__main__':
    diagrams_name = ["Logic View",
                    "Process View",
                    "Development View",
                    "Physical View",
                    "Scenario View"]
    with open("C:\\Research\\MAAD\\demo\\demo_v2\\output\\Modeler\\AV_1.txt") as f:
        content = f.read()
    uml_matches = re.findall(r"@startuml(.*?)@enduml",  content, re.DOTALL)
    expected_diagram_count = len(diagrams_name)
    if len(uml_matches) != expected_diagram_count:
        print(f"Warning: Expected {expected_diagram_count} diagrams, but found {len(uml_matches)}.")
    index = 0
    for diagram in diagrams_name:
        uml_content = f"@startuml{uml_matches[index]}@enduml"
        output = render(
        uml_content,
        engine='plantuml',
        format='svg',
        cacheopts={
            'use_cache': False
        })
        file_name = os.path.join(
            r"C:\\Research\\MAAD\\demo\\demo_v2\\output\\Modeler",
            f"{diagram.replace(' ', '_')}.svg"
        )
        # 确保目录存在
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        # 保存文件
        with open(file_name, "wb") as f:
            f.write(output[0])
        index = index + 1