import os
import re

replacements = {
    r'app\.modules\.sequence_service': r'app.scanner.input.sequence_validator',
    r'app\.modules\.candidate_generator': r'app.scanner.models.candidate_generator',
    r'app\.modules\.results_assembler': r'app.scoring.results_assembler',
    r'app\.modules\.cleavage_model': r'app.scoring.cleavage_model',
    r'app\.modules\.geometry_model': r'app.scoring.geometry_model',
    r'app\.modules\.thermodynamics_model': r'app.scoring.thermodynamics_model',
    r'app\.modules\.specificity_engine': r'app.scoring.specificity_engine',
    r'app\.modules\.shannon_entropy_weighter': r'app.scoring.shannon_entropy_weighter'
}

def replace_imports():
    for root, dirs, files in os.walk('.'):
        if 'node_modules' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if not file.endswith('.py'): continue
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            orig_content = content
            for old, new in replacements.items():
                content = re.sub(old, new, content)
                
            if content != orig_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated {path}")

if __name__ == '__main__':
    replace_imports()
