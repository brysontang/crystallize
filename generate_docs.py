from lazydocs import generate_docs
import os
import pkgutil
import crystallize
import importlib

paths = [f'crystallize.{name}' for _, name, _ in pkgutil.iter_modules(crystallize.__path__)]
output_dir = './docs/src/content/docs/reference'
os.makedirs(output_dir, exist_ok=True)

for path in paths:
    module_name = path.split('.')[-1] if '.' in path else path
    md_file = f'{output_dir}/{module_name}.md'
    
    # Dynamically import the module
    module = importlib.import_module(path)
    
    # Generate MD content as string
    from lazydocs import MarkdownGenerator
    generator = MarkdownGenerator(src_base_url='https://github.com/brysontang/crystallize/blob/main/')  # Use kwarg for src_base_url
    md_content = generator.import2md(module)
    
    md_content = md_content.replace(f"# <kbd>module</kbd> `{path}`\n", f"## <kbd>module</kbd> `{path}`\n", 1)  # If it's a h2 heading

    # Add frontmatter
    frontmatter = f'---\ntitle: {module_name.capitalize()}\n---\n\n'
    
    # Write to file
    with open(md_file, 'w') as f:
        f.write(frontmatter + md_content)