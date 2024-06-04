import os
from bs4 import BeautifulSoup
import html2text

def convert_html_to_markdown(html_content, link_mapping):
    h = html2text.HTML2Text()
    h.ignore_links = False

    # Update internal links to point to the relevant sections in the Markdown
    soup = BeautifulSoup(html_content, 'html.parser')
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href in link_mapping:
            a['href'] = f"#{link_mapping[href]}"
    
    return h.handle(str(soup))

def create_link_mapping(root_dir):
    link_mapping = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == "index.html":
                relative_path = os.path.relpath(os.path.join(subdir, file), root_dir)
                chapter_id = relative_path.replace(os.sep, '-').replace('index.html', '')
                link_mapping[relative_path] = chapter_id
                link_mapping[relative_path.replace(os.sep, '/')] = chapter_id  # for URLs with slashes
    return link_mapping

def read_html_files(root_dir, link_mapping):
    markdown_content = []
    
    for subdir, _, files in os.walk(root_dir):
        relative_path = os.path.relpath(subdir, root_dir)
        if files and any(file == "index.html" for file in files):
            # Add directory as a heading based on its depth
            heading_level = relative_path.count(os.sep) + 1
            markdown_content.append(f"{'#' * heading_level} {relative_path}\n")
        
        for file in files:
            if file == "index.html":
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    title = soup.title.string if soup.title else "No Title"
                    chapter_id = os.path.relpath(file_path, root_dir).replace(os.sep, '-').replace('index.html', '')
                    markdown_content.append(f"<a id='{chapter_id}'></a>\n")
                    markdown_content.append(f"{'#' * (heading_level + 1)} {title}\n")
                    markdown_content.append(convert_html_to_markdown(html_content, link_mapping))
    
    return "\n".join(markdown_content)

def save_to_markdown_file(content, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    root_dir =  "./v2realbot/static/js/vbt/"
    output_file = "output.md"
    link_mapping = create_link_mapping(root_dir)
    markdown_content = read_html_files(root_dir, link_mapping)
    save_to_markdown_file(markdown_content, output_file)
    print(f"Markdown document created at {output_file}")

if __name__ == "__main__":
    main()
