import os

from jinja2 import Environment, FileSystemLoader


def render_html_page(json_rendered, template_path, template_filename, output_dir):
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template(template_filename)

    # Render the template with the data
    html_output = template.render(header=json_rendered['header'], movies=json_rendered['content'],
                                  initial_count=50, batch_size=30)

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, 'movies.html')

    # Save the output to an HTML file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(html_output)

    print("HTML page generated successfully!")
    return output_file_path
