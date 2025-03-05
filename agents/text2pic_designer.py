from plantweb.render import render
import re
import os

if __name__ == '__main__':
    diagrams_name = {"Logic View":["Class Diagram", "Object Diagram", "State Diagram"],
                    "Development View":["Package Diagram", "Component Diagram"],
                    "Process View":["Activity Diagram", "Sequence Diagram", "Collaboration Diagram"],
                    "Physical View":["Deployment Diagram", "Container Diagram"],
                    "Scenario View":["Use Case Diagram"]}
    with open("C:\\Research\\MAAD\\demo\\demo_v2\\output\\Designer\\UML_1.txt") as f:
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
            file_name = os.path.join(
                r"C:\\Research\\MAAD\\demo\\demo_v2\\output\\Designer",
                f"{view}_{diagram.replace(' ', '_')}.svg"
            )
            # 确保目录存在
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            # 保存文件
            with open(file_name, "wb") as f:
                f.write(output[0])
            index = index + 1